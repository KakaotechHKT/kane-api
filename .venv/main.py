import mysql.connector
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional, List, Union

app = FastAPI()

# DB 연결 설정 - 로컬
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "mysql",
    "database": "hackathon_temp"
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
    menu: List[Dict[str, str]]  # JSON 리스트 형태로 변환

# /chat 응답 모델
class ChatResponse(BaseModel):
    httpStatusCode: int
    message: str
    data: Dict[str, int]  # chatID 포함

# /chat/chatting 응답 모델
class RestaurantResponse(BaseModel):
    httpStatusCode: int
    message: str
    chat: Optional[str] = None
    placeList: Optional[List[Restaurant]] = None

# 카테고리 데이터 모델
class Category(BaseModel):
    main: str
    keywords: str

# 채팅 데이터 요청 모델
class ChatData(BaseModel):
    chatID: int
    category: Optional[Category] = None
    chat: Optional[str] = None

# /chat - 새로운 채팅방 생성
@app.get("/chat", response_model=ChatResponse, status_code=200)
async def create_chat():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 새로운 채팅방 추가
        cursor.execute("INSERT INTO chat () VALUES ()")
        conn.commit()

        # 생성된 chatID 가져오기
        chat_id = cursor.lastrowid

        cursor.close()
        conn.close()

        response = ChatResponse(
            httpStatusCode=200,
            message="채팅방 개설에 성공하였습니다.",
            data={"chatID": chat_id}  # data 필드 추가
        )
        return response

    except Exception as e:
        print(f"오류 발생: {e}")
        raise HTTPException(
            status_code=500,
            detail=ChatResponse(
                httpStatusCode=500,
                message="내부 서버 오류입니다.",
                data={"chatID": -1}
            ).dict()
        )

# /chat/chatting - 유저 데이터 저장 후 추천 식당 정보 반환
@app.post("/chat/chatting", response_model=RestaurantResponse, status_code=200)
async def save_chat(chat_data: ChatData):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        chat_id = chat_data.chatID
        ctg1 = chat_data.category.main if chat_data.category else None
        ctg2 = chat_data.category.keywords if chat_data.category else None
        chat_text = chat_data.chat if chat_data.chat else None

        # 채팅 데이터 저장
        cursor.execute(
            "INSERT INTO chat_chatting (chatID, ctg1, ctg2, chat) VALUES (%s, %s, %s, %s)",
            (chat_id, ctg1, ctg2, chat_text)
        )
        conn.commit()

        ##### 바로 윗줄에서 유저 정보 저장했습니다 #####
        ##### 이 공간에서 식당 ID를 가져오면 될 것 같습니다 #####

        # 식당 정보 가져오기
        restaurant_ids = []
        ids = [10, 20, 30] # ID 예시
        for id in ids: restaurant_ids.append(id)
        format_strings = ",".join(["%s"] * len(restaurant_ids))
        cursor.execute(f"SELECT * FROM restaurants WHERE id IN ({format_strings})", restaurant_ids)
        restaurants = cursor.fetchall()

        # 식당 정보 나열
        place_list = []
        for restaurant in restaurants:
            place_list.append(Restaurant(
                id=restaurant["id"],
                name=restaurant["name"],
                mainCategory=restaurant["ctg1"],
                subCategory=restaurant["ctg2"],
                latitude=float(restaurant["latitude"]) if restaurant["latitude"] is not None else None,
                longitude=float(restaurant["longitude"]) if restaurant["longitude"] is not None else None,
                url=restaurant["kakao_link"],
                menu=json.loads(restaurant["menu"]) if restaurant["menu"] else []  # JSON 문자열 → 리스트 변환
            ))

        cursor.close()
        conn.close()

        response = RestaurantResponse(
            httpStatusCode=200,
            message="채팅 값 전달드립니다.",
            chat=chat_text if chat_text else "",
            placeList=place_list if place_list else None
        )
        return response

    except Exception as e:
        print(f"오류 발생: {e}")
        raise HTTPException(
            status_code=500,
            detail=RestaurantResponse(
                httpStatusCode=500,
                message="내부 서버 오류입니다.",
                chat="",
                placeList=None
            ).dict()
        )
