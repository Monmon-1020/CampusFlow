#!/usr/bin/env python3

import asyncio
import requests
import json

# Test configuration
API_BASE_URL = "http://localhost:8000"

def test_auth():
    """Test authentication to get a token"""
    print("🔐 Testing authentication...")
    
    # Use dev/super admin login
    response = requests.post(f"{API_BASE_URL}/api/auth/super_admin/login")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Authentication successful")
        return data.get('access_token')
    else:
        print(f"❌ Authentication failed: {response.status_code} {response.text}")
        return None

def test_stream_creation(token):
    """Create a test stream for brainstorming"""
    print("📚 Testing stream creation...")
    
    headers = {'Authorization': f'Bearer {token}'}
    data = {
        'name': 'Test Brainstorm Class',
        'description': 'Test class for brainstorming',
        'stream_type': 'class',
        'class_name': '1年A組',
        'grade': 1,
        'is_public': True,
        'allow_student_posts': True
    }
    
    response = requests.post(f"{API_BASE_URL}/api/streams", headers=headers, data=data)
    
    if response.status_code == 200:
        stream_data = response.json()
        stream_id = stream_data.get('id')
        print(f"✅ Stream created: {stream_id}")
        return stream_id
    else:
        print(f"❌ Stream creation failed: {response.status_code} {response.text}")
        return None

def test_brainstorm_session(token, stream_id):
    """Test brainstorming session creation and flow"""
    print("🧠 Testing brainstorming session...")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # 1. Create session
    print("  1. Creating brainstorm session...")
    response = requests.post(
        f"{API_BASE_URL}/api/brainstorm/sessions",
        headers=headers,
        json={'stream_id': stream_id}
    )
    
    if response.status_code != 200:
        print(f"❌ Session creation failed: {response.status_code} {response.text}")
        return False
    
    session_data = response.json()
    session_id = session_data.get('session_id')
    print(f"✅ Session created: {session_id}")
    
    # 2. Get session data
    print("  2. Getting session data...")
    response = requests.get(
        f"{API_BASE_URL}/api/brainstorm/sessions/{session_id}",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ Get session failed: {response.status_code} {response.text}")
        return False
    
    session_details = response.json()
    print(f"✅ Session data retrieved, state: {session_details.get('state')}")
    
    # 3. Submit ideas
    print("  3. Submitting test ideas...")
    ideas = [
        "学食のメニューを増やす",
        "Wi-Fiを高速化する",
        "自習室を24時間開放する",
        "オンライン授業の録画を見られるようにする",
        "部活動の予算を増やす"
    ]
    
    idea_ids = []
    for idea in ideas:
        response = requests.post(
            f"{API_BASE_URL}/api/brainstorm/sessions/{session_id}/ideas",
            headers=headers,
            json={'text': idea}
        )
        
        if response.status_code == 200:
            idea_data = response.json()
            idea_ids.append(idea_data.get('idea_id'))
            print(f"  ✅ Idea submitted: {idea}")
        else:
            print(f"  ❌ Idea submission failed: {response.text}")
    
    # 4. Create group
    print("  4. Creating test group...")
    response = requests.post(
        f"{API_BASE_URL}/api/brainstorm/sessions/{session_id}/groups",
        headers=headers,
        json={'title': '学習環境改善'}
    )
    
    if response.status_code != 200:
        print(f"❌ Group creation failed: {response.status_code} {response.text}")
        return False
    
    group_data = response.json()
    group_id = group_data.get('group_id')
    print(f"✅ Group created: {group_id}")
    
    # 5. Move idea to group
    if idea_ids and group_id:
        print("  5. Moving idea to group...")
        response = requests.post(
            f"{API_BASE_URL}/api/brainstorm/sessions/{session_id}/move",
            headers=headers,
            json={'idea_id': idea_ids[0], 'group_id': group_id}
        )
        
        if response.status_code == 200:
            print("✅ Idea moved to group successfully")
        else:
            print(f"❌ Move idea failed: {response.text}")
    
    # 6. Start voting
    print("  6. Starting voting phase...")
    response = requests.post(
        f"{API_BASE_URL}/api/brainstorm/sessions/{session_id}/start-voting",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ Start voting failed: {response.status_code} {response.text}")
        return False
    
    print("✅ Voting phase started")
    
    # 7. Cast votes
    print("  7. Casting test votes...")
    if group_id:
        response = requests.post(
            f"{API_BASE_URL}/api/brainstorm/sessions/{session_id}/vote",
            headers=headers,
            json={'target_id': group_id, 'target_type': 'group'}
        )
        
        if response.status_code == 200:
            vote_data = response.json()
            print(f"✅ Vote cast, remaining: {vote_data.get('remaining_votes')}")
        else:
            print(f"❌ Voting failed: {response.text}")
    
    # 8. End session
    print("  8. Ending session...")
    response = requests.post(
        f"{API_BASE_URL}/api/brainstorm/sessions/{session_id}/end",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ End session failed: {response.status_code} {response.text}")
        return False
    
    summary = response.json()
    print(f"✅ Session ended, summary type: {summary.get('type')}")
    
    # 9. Save summary
    print("  9. Saving summary to stream...")
    response = requests.post(
        f"{API_BASE_URL}/api/brainstorm/sessions/{session_id}/save",
        headers=headers,
        json={'title': 'テストブレインストーミング結果'}
    )
    
    if response.status_code == 200:
        save_data = response.json()
        print(f"✅ Summary saved to announcement: {save_data.get('announcement_id')}")
        return True
    else:
        print(f"❌ Save summary failed: {response.text}")
        return False

def main():
    """Run all tests"""
    print("🧪 Starting brainstorming feature tests...")
    print("="*50)
    
    # Get auth token
    token = test_auth()
    if not token:
        print("❌ Cannot proceed without authentication")
        return
    
    # Create test stream
    stream_id = test_stream_creation(token)
    if not stream_id:
        print("❌ Cannot proceed without stream")
        return
    
    # Test brainstorming flow
    success = test_brainstorm_session(token, stream_id)
    
    print("="*50)
    if success:
        print("🎉 All brainstorming tests passed!")
        print("\n✨ Ready to test the frontend:")
        print("   1. Open http://localhost:3001")
        print("   2. Login as super admin")
        print("   3. Go to Streams tab")
        print("   4. Select a stream")
        print("   5. Click '🧠 ブレスト開始' button")
        print("   6. Follow the brainstorming flow!")
    else:
        print("❌ Some tests failed. Check the logs above.")

if __name__ == "__main__":
    main()