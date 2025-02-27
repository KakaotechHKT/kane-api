import mysql.connector
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional, List, Union

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인에서 접근 허용
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

# DB 연결 설정 - 로컬
db_config = {
    "host": "babpat-db.c5a0q02qmhx6.ap-northeast-2.rds.amazonaws.com",
    "user": "babpat",
    "password": "babpat1!",
    "database": "babpat"
}

# DB 연결 함수
def get_db_connection():
    return mysql.connector.connect(**db_config)

# 식당 개별 정보 모델
class Restaurant(BaseModel):
    id: int
    name: str
    mainCategory: str # 리스트 변환 안함
    subCategory: str # 리스트 변환 안함
    latitude: Optional[float]  # 값이 NULL인 경우 발견 -> Optional 사용
    longitude: Optional[float]
    url: str
    thumbnail: Optional[str]
    menu: List[Dict[str, Union[str, int]]]  # JSON 리스트 형태로 변환

# /chat/chatting 응답 모델
class RestaurantResponse(BaseModel):
    httpStatusCode: int
    message: Optional[str] = None
    data: Optional[Dict[str, Union[int, str, List[Restaurant]]]] = None

# 카테고리 데이터 모델
class Category(BaseModel):
    main: Optional[str] = None
    keywords: Optional[str] = None

# 채팅 데이터 요청 모델
class ChatData(BaseModel):
    chatID: int
    category: Optional[Category] = None
    chat: Optional[str] = None

# /chat - 새로운 채팅방 생성
@app.post("/chat", response_model=RestaurantResponse, status_code=200)
async def create_chat():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 새로운 채팅방 추가
        cursor.execute("INSERT INTO chat () VALUES ()")
        conn.commit()

        # 생성된 chatID 가져오기
        chat_id = cursor.lastrowid

        # 식당 정보 가져오기
        restaurant_ids = []

        ##################################################
        ##### 광고 식당 ID #####
        suggest_restaurant_ids = []  # ID 입력
        ##################################################

        for id in suggest_restaurant_ids:
            restaurant_ids.append(id)

        place_list = []

        # restaurant_ids가 비어 있지 않을 때만 쿼리 실행
        if restaurant_ids:
            format_strings = ",".join(["%s"] * len(restaurant_ids))
            cursor.execute(f"SELECT * FROM restaurant WHERE restaurant_id IN ({format_strings})", restaurant_ids)
            restaurants = cursor.fetchall()

            # 식당 정보 나열
            place_list = [
                Restaurant(
                    id=restaurant["restaurant_id"],
                    name=restaurant["name"],
                    mainCategory=restaurant["category1"],
                    subCategory=restaurant["category2"],
                    latitude=float(restaurant["latitude"]) if restaurant["latitude"] is not None else None,
                    longitude=float(restaurant["longitude"]) if restaurant["longitude"] is not None else None,
                    url=restaurant["kakao_link"],
                    thumbnail=restaurant["thumbnail"] if restaurant["thumbnail"] is not None else None,
                    menu=[{**item, "price": int(item["price"])} for item in json.loads(restaurant["menus"]) if
                          restaurant["menus"]]
                ) for restaurant in restaurants
            ]

        cursor.close()
        conn.close()

        response = RestaurantResponse(
            httpStatusCode=200,
            message="채팅방 개설에 성공하였습니다.",
            data={
                "chatID": chat_id,
                "placeList": place_list
            }
        )
        return response

    except Exception as e:
        print(f"오류 발생: {e}")
        raise HTTPException(
            status_code=500,
            detail=RestaurantResponse(
                httpStatusCode=500,
                message="내부 서버 오류입니다.",
                data=None
            ).dict()
        )

# /chat/chatting - 유저 데이터 저장 후 추천 식당 정보 반환
@app.post("/chat/chatting", response_model=RestaurantResponse, status_code=200)
async def save_chat(chat_data: ChatData):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        chat_id = chat_data.chatID
        ctg1 = chat_data.category.main if chat_data.category and chat_data.category.main else None
        ctg2 = chat_data.category.keywords if chat_data.category and chat_data.category.keywords else None
        chat_text = chat_data.chat if chat_data.chat else None
        
        ##################################################
        ##### AI 모델 응답 - 채팅
        ai_chat = "이곳에 AI 답변이 들어가면 될 것 같습니다"
        chat_text = ai_chat
        ##################################################

        # 채팅 데이터 저장
        cursor.execute(
            "INSERT INTO chat_chatting (chatID, ctg1, ctg2, chat) VALUES (%s, %s, %s, %s)",
            (chat_id, ctg1, ctg2, chat_text)
        )
        conn.commit()
        
        ##################################################
        ##### AI 모델 응답 - 추천 식당 리스트
        ##################################################

        # 식당 정보 가져오기
        restaurant_ids = []
        ids = [10, 20, 30] # ID 예시
        for id in ids: restaurant_ids.append(id)  # ID 예시
        format_strings = ",".join(["%s"] * len(restaurant_ids))
        cursor.execute(f"SELECT * FROM restaurant WHERE restaurant_id IN ({format_strings})", restaurant_ids)
        restaurants = cursor.fetchall()

        # 식당 정보 나열
        place_list = [
            Restaurant(
                id=restaurant["restaurant_id"],
                name=restaurant["name"],
                mainCategory=restaurant["category1"],
                subCategory=restaurant["category2"],
                latitude=float(restaurant["latitude"]) if restaurant["latitude"] is not None else None,
                longitude=float(restaurant["longitude"]) if restaurant["longitude"] is not None else None,
                url=restaurant["kakao_link"],
                thumbnail=restaurant["thumbnail"] if restaurant["thumbnail"] is not None else None,
                menu=[{**item, "price": int(item["price"])} for item in json.loads(restaurant["menus"]) if
                      restaurant["menus"]]
            ) for restaurant in restaurants
        ]

        cursor.close()
        conn.close()

        response = RestaurantResponse(
            httpStatusCode=200,
            message="채팅 값 전달드립니다.",
            data={
                "chat": chat_text if chat_text else "",
                "placeList": place_list if place_list else None
            }
        )
        return response

    except Exception as e:
        print(f"오류 발생: {e}")
        raise HTTPException(
            status_code=500,
            detail=RestaurantResponse(
                httpStatusCode=500,
                message="내부 서버 오류입니다.",
                data=None
            ).dict()
        )