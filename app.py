import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# 從環境變數讀取金鑰 (保護隱私)
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

scheduler = BackgroundScheduler()
scheduler.start()

def send_remind(user_id, msg):
    # 多樣化提醒：使用 Flex Message (卡片樣式)
    flex_content = {
      "type": "bubble",
      "body": {
        "type": "box", "layout": "vertical",
        "contents": [{"type": "text", "text": "⏰ 提醒時間到！", "weight": "bold", "size": "xl"},
                     {"type": "text", "text": msg, "margin": "md"}]
      }
    }
    line_bot_api.push_message(user_id, FlexSendMessage(alt_text="提醒通知", contents=flex_content))

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text
    user_id = event.source.user_id

    if "提醒我" in text:
        # 重複提醒功能：每 1 小時觸發一次 (範例)
        scheduler.add_job(send_remind, 'interval', hours=1, args=[user_id, text], id=user_id)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="好的！已為您設定重複提醒。"))
    elif "停止" in text:
        scheduler.remove_job(user_id)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="已停止所有提醒。"))

if __name__ == "__main__":
    app.run()
