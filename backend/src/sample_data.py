"""
新規ユーザー向けサンプルデータ生成機能
"""
from datetime import datetime, timedelta
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from .models import Assignment, AssignmentLog, Event, User


async def create_sample_assignments_for_user(
    session: AsyncSession, user: User
) -> List[Assignment]:
    """新規ユーザー向けサンプル課題を作成"""

    # 既に課題が存在するかチェック
    statement = select(Assignment).where(Assignment.created_by == user.id)
    result = await session.exec(statement)
    existing = result.all()

    if existing:
        return existing  # 既存の課題がある場合はそのまま返す

    today = datetime.utcnow()

    sample_assignments = [
        Assignment(
            title=f"{user.name}さんへ：CampusFlowへようこそ！",
            subject="システム案内",
            description="CampusFlowの使い方を確認して、学習管理を始めましょう。ダッシュボードで課題の進捗を確認し、イベントページで予定をチェックできます。",
            due_at=today + timedelta(days=7),
            created_by=user.id,
        ),
        Assignment(
            title="数学の基本問題",
            subject="数学",
            description="二次関数のグラフを描いて、頂点と軸の方程式を求めてください。教科書p.45-48の例題を参考にしてください。",
            due_at=today + timedelta(days=3),
            created_by=user.id,
        ),
        Assignment(
            title="英語読解レポート",
            subject="英語",
            description="指定された英文を読んで、内容について400語程度の英語で感想を書いてください。文法と語彙の正確性に注意してください。",
            due_at=today + timedelta(days=5),
            created_by=user.id,
        ),
        Assignment(
            title="理科実験レポート",
            subject="理科",
            description="化学反応の実験結果をまとめ、考察を含めたレポートを作成してください。実験データの正確な記録が重要です。",
            due_at=today + timedelta(days=10),
            created_by=user.id,
        ),
    ]

    for assignment in sample_assignments:
        session.add(assignment)

    await session.commit()

    # 作成された課題を取得して返す
    for assignment in sample_assignments:
        await session.refresh(assignment)

    return sample_assignments


async def create_sample_events_for_user(
    session: AsyncSession, user: User
) -> List[Event]:
    """新規ユーザー向けサンプルイベントを作成"""

    # 既にイベントが存在するかチェック
    statement = select(Event).where(Event.created_by == user.id)
    result = await session.exec(statement)
    existing = result.all()

    if existing:
        return existing  # 既存のイベントがある場合はそのまま返す

    today = datetime.utcnow()

    sample_events = [
        Event(
            title=f"{user.name}さんのCampusFlow開始記念",
            description="学習管理システムの利用開始を記念して！効率的な学習計画を立てて目標を達成しましょう。",
            category="academic",
            location="オンライン",
            start_at=today,
            end_at=today + timedelta(hours=1),
            created_by=user.id,
        ),
        Event(
            title="中間テスト期間",
            description="各科目の中間テストが実施されます。計画的に準備を進めましょう。",
            category="academic",
            location="各教室",
            start_at=today + timedelta(days=14),
            end_at=today + timedelta(days=18),
            created_by=user.id,
        ),
        Event(
            title="体育祭",
            description="年に一度の体育祭です。クラス対抗リレーや綱引きなど、様々な競技を予定しています。",
            category="sports",
            location="校庭・体育館",
            start_at=today + timedelta(days=21),
            end_at=today + timedelta(days=21, hours=6),
            created_by=user.id,
        ),
        Event(
            title="文化祭準備",
            description="文化祭の出し物準備を行います。各クラスで企画を練って素晴らしい発表を目指しましょう。",
            category="cultural",
            location="各教室",
            start_at=today + timedelta(days=28),
            end_at=today + timedelta(days=28, hours=3),
            created_by=user.id,
        ),
        Event(
            title="進路相談会",
            description="進路について個別相談を行います。将来の目標について一緒に考えましょう。",
            category="administrative",
            location="進路指導室",
            start_at=today + timedelta(days=35),
            end_at=today + timedelta(days=35, hours=2),
            created_by=user.id,
        ),
    ]

    for event in sample_events:
        session.add(event)

    await session.commit()

    # 作成されたイベントを取得して返す
    for event in sample_events:
        await session.refresh(event)

    return sample_events


async def ensure_user_has_sample_data(session: AsyncSession, user: User):
    """ユーザーにサンプルデータがあることを保証する"""

    # 課題をチェックして、必要に応じて作成
    assignments = await create_sample_assignments_for_user(session, user)

    # イベントをチェックして、必要に応じて作成
    events = await create_sample_events_for_user(session, user)

    return {
        "assignments_created": len(assignments),
        "events_created": len(events),
        "message": f"ユーザー {user.name} のサンプルデータを準備しました",
    }


async def create_assignment_sample_logs(
    session: AsyncSession, user: User, assignment: Assignment
):
    """サンプル課題に対する進捗ログを作成"""

    # 既にログが存在するかチェック
    statement = select(AssignmentLog).where(
        AssignmentLog.assignment_id == assignment.id, AssignmentLog.user_id == user.id
    )
    result = await session.exec(statement)
    existing_log = result.first()

    if existing_log:
        return existing_log

    # 課題の種類に応じてサンプルログを作成
    if "ようこそ" in assignment.title:
        # ウェルカム課題は「進行中」
        status = "in_progress"
        notes = "CampusFlowの機能を確認中です。"
    elif "数学" in assignment.subject:
        # 数学課題は「開始済み」
        status = "started"
        notes = "教科書の例題を確認しました。"
    else:
        # その他は「未開始」
        status = "not_started"
        notes = ""

    log = AssignmentLog(
        assignment_id=assignment.id,
        user_id=user.id,
        status=status,
        notes=notes,
    )

    session.add(log)
    await session.commit()
    await session.refresh(log)

    return log
