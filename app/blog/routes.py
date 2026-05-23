import os
import uuid
import bleach
import markdown
from flask import Blueprint, render_template, redirect, flash, url_for, request, abort, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from .. import db, mail
from ..models import Post, Tag, Comment, Like, Bookmark, User
from .forms import PostForm
from flask_mail import Message

blog = Blueprint('blog', __name__)

ALLOWED_TAGS = [
    'p', 'strong', 'em', 'ul', 'ol', 'li', 'a', 'code', 'pre', 'blockquote',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6'
]
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target'],
    'code': ['class'],
}


def sanitize_markdown(raw_text):
    safe_text = bleach.clean(raw_text or '', tags=[], attributes={}, strip=True)
    html = markdown.markdown(safe_text, extensions=['extra', 'fenced_code'])
    return bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)


@blog.app_template_filter('render_markdown')
def render_markdown_filter(text):
    return sanitize_markdown(text)


def save_thumbnail(thumbnail_file):
    if not thumbnail_file or not hasattr(thumbnail_file, 'filename') or thumbnail_file.filename == '':
        return None
    filename = secure_filename(thumbnail_file.filename)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    upload_folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)
    path = os.path.join(upload_folder, unique_name)
    thumbnail_file.save(path)
    return unique_name


def get_or_create_tags(tag_string):
    tags = []
    if not tag_string:
        return tags
    for raw_name in tag_string.split(','):
        name = raw_name.strip().lower()
        if not name:
            continue
        tag = Tag.query.filter_by(name=name).first()
        if not tag:
            tag = Tag(name=name)
        tags.append(tag)
    return tags


@blog.route('/')
def home():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('q', '')
    tag_name = request.args.get('tag', '')

    posts_query = Post.query
    if search_query:
        posts_query = posts_query.filter(
            db.or_(
                Post.title.ilike(f'%{search_query}%'),
                Post.content.ilike(f'%{search_query}%')
            )
        )
    if tag_name:
        posts_query = posts_query.join(Post.tags).filter(Tag.name == tag_name)

    posts = posts_query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    tags = Tag.query.order_by(Tag.name).all()
    return render_template('home.html', posts=posts, tags=tags, search_query=search_query, selected_tag=tag_name)


@blog.route('/create', methods=['GET', 'POST'])
@login_required
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        content = bleach.clean(form.content.data or '', tags=[], attributes={}, strip=True)
        post = Post(
            title=form.title.data,
            content=content,
            user_id=current_user.id,
            thumbnail=save_thumbnail(form.thumbnail.data)
        )
        post.tags = get_or_create_tags(form.tags.data)
        db.session.add(post)
        db.session.commit()
        flash('Post created!', 'success')
        return redirect(url_for('blog.view_post', post_id=post.id))
    return render_template("create_post.html", form=form)

@blog.route('/dashboard')
@login_required
def dashboard():
    posts = Post.query.filter_by(user_id=current_user.id).order_by(Post.date_posted.desc()).all()
    bookmarks = Bookmark.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', user=current_user, posts=posts, bookmarks=bookmarks)


@blog.route('/post/<int:post_id>')
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    post.view_count += 1
    db.session.commit()

    post_html = sanitize_markdown(post.content)
    comments = Comment.query.filter_by(post_id=post.id, parent_id=None).order_by(Comment.date_posted.asc()).all()
    return render_template('view_post.html', post=post, post_html=post_html, comments=comments)

@blog.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm(obj=post)
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = bleach.clean(form.content.data or '', tags=[], attributes={}, strip=True)
        if form.thumbnail.data:
            new_thumbnail = save_thumbnail(form.thumbnail.data)
            if new_thumbnail:
                post.thumbnail = new_thumbnail
        post.tags = get_or_create_tags(form.tags.data)
        db.session.commit()
        flash('Post updated!', 'success')
        return redirect(url_for('blog.view_post', post_id=post.id))
    form.tags.data = ', '.join([tag.name for tag in post.tags])
    return render_template('edit_post.html', form=form, post=post)

@blog.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    body = bleach.clean(request.form.get('body', ''), tags=[], attributes={}, strip=True)
    if not body:
        flash('Comment cannot be empty.', 'warning')
        return redirect(url_for('blog.view_post', post_id=post.id))

    parent_id = request.form.get('parent_id')
    comment = Comment(body=body, user_id=current_user.id, post_id=post.id)
    if parent_id:
        parent = Comment.query.get(parent_id)
        if parent and parent.post_id == post.id:
            comment.parent = parent
    db.session.add(comment)
    db.session.commit()
    flash('Comment added.', 'success')

    if post.author and post.author.email:
        try:
            msg = Message(
                subject=f'New comment on: {post.title}',
                recipients=[post.author.email],
                body=f'{current_user.name} commented on your post. View it at {url_for("blog.view_post", post_id=post.id, _external=True)}'
            )
            mail.send(msg)
        except Exception:
            pass

    return redirect(url_for('blog.view_post', post_id=post.id))


@blog.route('/post/<int:post_id>/like', methods=['POST'])
@login_required
def toggle_like(post_id):
    post = Post.query.get_or_404(post_id)
    like = Like.query.filter_by(user_id=current_user.id, post_id=post.id).first()
    if like:
        db.session.delete(like)
        flash('Removed like.', 'info')
    else:
        db.session.add(Like(user_id=current_user.id, post_id=post.id))
        flash('Post liked.', 'success')
    db.session.commit()
    return redirect(url_for('blog.view_post', post_id=post.id))


@blog.route('/post/<int:post_id>/bookmark', methods=['POST'])
@login_required
def toggle_bookmark(post_id):
    post = Post.query.get_or_404(post_id)
    bookmark = Bookmark.query.filter_by(user_id=current_user.id, post_id=post.id).first()
    if bookmark:
        db.session.delete(bookmark)
        flash('Bookmark removed.', 'info')
    else:
        db.session.add(Bookmark(user_id=current_user.id, post_id=post.id))
        flash('Bookmarked post.', 'success')
    db.session.commit()
    return redirect(url_for('blog.view_post', post_id=post.id))


@blog.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted.', 'info')
    return redirect(url_for('blog.home'))


@blog.route('/profile/<int:user_id>')
def profile(user_id):
    user = User.query.get_or_404(user_id)
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.date_posted.desc()).all()
    return render_template('profile.html', profile_user=user, posts=posts)


@blog.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin():
        abort(403)

    total_posts = Post.query.count()
    total_users = User.query.count()
    total_likes = Like.query.count()
    total_views = db.session.query(db.func.sum(Post.view_count)).scalar() or 0
    popular_posts = Post.query.order_by(Post.view_count.desc()).limit(5).all()
    most_liked = Post.query.outerjoin(Like).group_by(Post.id).order_by(db.func.count(Like.id).desc()).limit(5).all()
    return render_template(
        'admin_dashboard.html',
        total_posts=total_posts,
        total_users=total_users,
        total_likes=total_likes,
        total_views=total_views,
        popular_posts=popular_posts,
        most_liked=most_liked
    )


@blog.route('/api/posts')
def api_posts():
    posts = Post.query.order_by(Post.date_posted.desc()).limit(20).all()
    return jsonify([
        {
            'id': post.id,
            'title': post.title,
            'summary': post.content[:160],
            'author': post.author.name if post.author else None,
            'created_at': post.date_posted.isoformat(),
            'views': post.view_count,
            'tags': [tag.name for tag in post.tags],
        }
        for post in posts
    ])


@blog.route('/api/posts/<int:post_id>')
def api_post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    return jsonify({
        'id': post.id,
        'title': post.title,
        'content': post.content,
        'author': post.author.name if post.author else None,
        'created_at': post.date_posted.isoformat(),
        'views': post.view_count,
        'tags': [tag.name for tag in post.tags],
        'likes': post.like_count(),
    })