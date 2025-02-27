# kane-api
임시 레포지토리

# DB 연결 설정 - babpat db에 맞도록 수정했습니다
db_config = {
    "host": "babpat-db.c5a0q02qmhx6.ap-northeast-2.rds.amazonaws.com",
    "user": "babpat",
    "password": "babpat1!",
    "database": "babpat"
}

/chat/chatting에서 json 입력 받을시 사용했던 id 재사용시 오류발생합니다!
primary key로 설정해 두어서 발생하는 오류이니 입력 받을때 id 재사용 없도록 확인바랍니다!
