from collections import Counter
from django.utils import timezone

def generate_session_summary(session):
    """
    Aggregate session stats and generate a plain-text summary from real data.
    No AI or external API required.
    """
    from .models import SessionSummary

    posts = session.posts.select_related('author').all()
    total_posts = posts.count()
    participants_count = session.participants.count()

    author_counts = Counter(post.author.username for post in posts)
    top_contributors = [
        {'username': username, 'post_count': count}
        for username, count in author_counts.most_common(3)
    ]

    try:
        from groups.models import GroupResource
        files_shared = GroupResource.objects.filter(
            group=session.group,
            uploaded_at__gte=session.start_time,
            uploaded_at__lte=session.end_time,
        ).count()
    except Exception:
        files_shared = 0

    if session.end_time and session.start_time:
        actual_minutes = int((session.end_time - session.start_time).total_seconds() / 60)
    else:
        actual_minutes = session.duration_minutes

    summary_lines = []
    summary_lines.append(
        f"• {participants_count} participant{'s' if participants_count != 1 else ''} "
        f"collaborated in this {actual_minutes}-minute session."
    )
    if total_posts > 0:
        summary_lines.append(
            f"• {total_posts} post{'s' if total_posts != 1 else ''} "
            f"{'were' if total_posts != 1 else 'was'} shared during the session."
        )
    if top_contributors:
        top_names = ', '.join(c['username'] for c in top_contributors[:3])
        summary_lines.append(
            f"• Most active contributor{'s' if len(top_contributors) > 1 else ''}: "
            f"{top_names}."
        )
    if files_shared > 0:
        summary_lines.append(
            f"• {files_shared} file{'s' if files_shared != 1 else ''} "
            f"{'were' if files_shared != 1 else 'was'} shared as resources."
        )
    if total_posts == 0:
        summary_lines.append("• No posts were made during this session.")

    auto_summary = '\n'.join(summary_lines)

    summary, _ = SessionSummary.objects.update_or_create(
        session=session,
        defaults={
            'total_posts': total_posts,
            'participants_count': participants_count,
            'files_shared': files_shared,
            'top_contributors': top_contributors,
            'auto_summary': auto_summary,
        }
    )
    return summary