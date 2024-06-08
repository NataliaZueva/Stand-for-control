from sqlalchemy.orm import Session
import models
import telebot
import paho.mqtt.client as client
from telebot import types
import random
import crud
from database import SessionLocal, engine
from fastapi import Depends, FastAPI
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery


def get_data(db: Session, chat_id: str):
    results = db.query(models.Data).filter(models.Data.chat_id == chat_id).all()
    return [i.token for i in results]


def create_data(db: Session, chat_id: str, token: str):
    db_data = models.Data(**{"chat_id": chat_id, "token": token})
    db.add(db_data)
    db.commit()
    db.refresh(db_data)
    return db_data


def on_message(client, userdata, message, ):
    data = str(message.payload.decode("utf-8"))
    data = data.split(" ")
    if data[1] == "stop":
        client_sub.loop_stop()
        return
    with SessionLocal() as db:
        for i in crud.get_chat_id(db, data[0]):
            bot.send_message(i, data[1])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


bot = telebot.TeleBot('7262866067:AAF0EYvrRH4_Fmprssdi9pFzEmAKLD0LQS4')
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

client_id_pub = f"pub-{random.randint(0, 100)}"
client_id_sub = f"sub-{random.randint(0, 100)}"

broker = "broker.emqx.io"
client_pub = client.Client(client.CallbackAPIVersion.VERSION2, client_id_pub)
client_pub.connect(broker)

client_sub = client.Client(client.CallbackAPIVersion.VERSION2, client_id_sub)
client_sub.on_message = on_message
client_sub.connect(broker)


# начальное окно спрашивает о действиях после команды /start
@bot.message_handler(commands=['start'])
def startBot(message):
    with SessionLocal() as db:
        if len(crud.get_data(db, message.chat.id)) == 0:
            bot.send_message(message.chat.id,
                             "Для начала работы вам необходимо зарегистрировать подставку\n"
                             "Введите индефикатор подставки")
        else:
            markup = types.ReplyKeyboardMarkup(row_width=1)
            button_removal = types.InlineKeyboardButton(text='Начать работу')
            markup.add(button_removal)
            bot.send_message(message.chat.id, "Хоть одна подставка уже зарегистрирована", reply_markup=markup)


@bot.message_handler(content_types=['text'])
def handle_text_message(message):
    text = message.text

    with SessionLocal() as db:
        if text == "Проверять нагревание":
            if len(crud.get_data(db, message.chat.id)) > 0:
                token = crud.get_active(db, message.chat.id)
                bot.send_message(message.chat.id, "Плата начала работать")
                client_pub.publish(token + "/command", "h")
                client_sub.subscribe(token)
                client_sub.loop_forever()
            else:
                bot.send_message(message.chat.id, "Вы не подключили плату")
        elif text == "Проверять охлаждение":
            if len(crud.get_data(db, message.chat.id)) > 0:
                token = crud.get_active(db, message.chat.id)
                bot.send_message(message.chat.id, "Плата начала работать")
                client_pub.publish(token + "/command", "c")
                client_sub.subscribe(token)
                client_sub.loop_forever()
            else:
                bot.send_message(message.chat.id, "Вы не подключили плату")
        elif text == "Изменить градусы":
            bot.send_message(message.chat.id,
                             "Вам необходимо ввести градусы в значении от 0 до 100\n"
                             "Если число будет не целочисленное или иметь лишние элементы "
                             "программа не сможет распознать это\n"
                             "Введите значение:")
        elif text == "Удалить активную подставку":
            bot.send_message(message.chat.id, "Удаление подставки прошло успешно\n"
                                              "Прошу пройти в смену платы и выбрать активную или добавить новую")
            # client_pub.publish(token + "/command", "d")
            crud.delete_data(db, message.chat.id)
        elif text == "Какая плата сейчас активна?":
            active_board = crud.get_active(db, message.chat.id)
            if active_board:
                bot.send_message(message.chat.id, f"Сейчас активна плата: {active_board}")
            else:
                bot.send_message(message.chat.id, "Нет активной платы")
        elif text == "Сменить плату":
            data = crud.get_data(db, message.chat.id)
            if len(data) == 0:
                bot.send_message(message.chat.id, "Плат нет")
            else:
                buttons = [InlineKeyboardButton(text=board, callback_data=f"change_board:{board}") for board in data]
                rows = [buttons[i:i + 1] for i in range(0, len(buttons), 1)]
                reply_markup = InlineKeyboardMarkup(rows)
                bot.send_message(message.chat.id, "Выберите плату:", reply_markup=reply_markup)
        elif text == "Добавить новую плату":
            # Ввод новой платы или создание активной которая уже есть
            bot.send_message(message.chat.id, "Введите новую плату для подключения:")
        elif text == "Как пользоваться?" or text == "Вернуться назад":
            bot.send_message(message.chat.id, "Перед началом работы с телеграмм ботом вы вводите идентификатор - "
                                              "номер платы для подключения к ней\n\n"
                                              "Плат может быть несколько, так же у вашей платы может быть "
                                              "несколько пользователей\n"
                                              "После перед вами выходит несколько команд, которые помогают "
                                              "общаться с платами \n\n")
            markup = types.ReplyKeyboardMarkup(row_width=2)
            button_hot = types.InlineKeyboardButton(text='Проверка нагревания')
            button_cold = types.InlineKeyboardButton(text='Проверка охлаждения')
            markup.add(button_hot, button_cold)

            button_change = types.InlineKeyboardButton(text='Смена платы')
            button_degree = types.InlineKeyboardButton(text='Изменение градусов')
            markup.add(button_change, button_degree)

            button_work = types.InlineKeyboardButton(text='Проверка работы платы')
            button_new = types.InlineKeyboardButton(text='Проверка активности')
            markup.add(button_work, button_new)

            button_removal = types.InlineKeyboardButton(text='Удаление активной подставки')
            markup.add(button_removal)

            bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
        elif text == "Проверка нагревания":
            bot.send_message(message.chat.id, "Проверка нагревания\n"
                                              "При проверки нагревания плата отправляет нам данные о том, что что-то "
                                              "горячее начинает остывать, это помогает узнавать комфортную температуры "
                                              "вещества (температура указывается отдельно)")
            markup = types.ReplyKeyboardMarkup(row_width=2)
            next_button = InlineKeyboardButton("Вернуться назад")
            next_button1 = InlineKeyboardButton("Закончить ознакомление")
            markup.add(next_button, next_button1)
            bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
        elif text == "Проверка охлаждения":
            bot.send_message(message.chat.id, "Проверка охлаждения\n"
                                              "При проверки охлаждения плата отправляет нам данные о том, что что-то "
                                              "холодное начинает нагреваться, это помогает узнавать комфортную "
                                              "температуру вещества (температура указывается отдельно)")
            markup = types.ReplyKeyboardMarkup(row_width=2)
            next_button = InlineKeyboardButton("Вернуться назад")
            next_button1 = InlineKeyboardButton("Закончить ознакомление")
            markup.add(next_button, next_button1)
            bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
        elif text == "Смена платы":
            bot.send_message(message.chat.id, "Смена платы\n"
                                              "При выборе данной фуункции перед вами открываются все платы которые "
                                              "доступны сейчас, данная функция позволяет переключиться на другую "
                                              "плату чтобы с ней взаимодействовать\n"
                                              "Если нет никакой привязанной платы, то программа об этом ему скажет")
            markup = types.ReplyKeyboardMarkup(row_width=2)
            next_button = InlineKeyboardButton("Вернуться назад")
            next_button1 = InlineKeyboardButton("Закончить ознакомление")
            markup.add(next_button, next_button1)
            bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
        elif text == "Изменение градусов":
            bot.send_message(message.chat.id, "Изменение градусов\n"
                                              "Данная функция позволяет вам задать температуру, "
                                              "которую подставка должна отслеживать")
            markup = types.ReplyKeyboardMarkup(row_width=2)
            next_button = InlineKeyboardButton("Вернуться назад")
            next_button1 = InlineKeyboardButton("Закончить ознакомление")
            markup.add(next_button, next_button1)
            bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
        elif text == "Проверка активности":
            bot.send_message(message.chat.id, "Проверка активности\n"
                                              "Данная функция может проверить, с какой платой мы работаем")
            markup = types.ReplyKeyboardMarkup(row_width=2)
            next_button = InlineKeyboardButton("Вернуться назад")
            next_button1 = InlineKeyboardButton("Закончить ознакомление")
            markup.add(next_button, next_button1)
            bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
        elif text == "Добавление новой платы":
            bot.send_message(message.chat.id, "Добавление новой платы\n"
                                              "Если у вас появилось новое устройство, вы можете добавить его сюда "
                                              "при помощи данной программы\n"
                                              "Если утройство уже привязанно оно станет активным")
            markup = types.ReplyKeyboardMarkup(row_width=2)
            next_button = InlineKeyboardButton("Вернуться назад")
            next_button1 = InlineKeyboardButton("Закончить ознакомление")
            markup.add(next_button, next_button1)
            bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
        elif text == "Удаление активной подставки":
            bot.send_message(message.chat.id, "Удаление активной подставки\n"
                                              "Если подставка стала не нужна или есть на то другие причины, "
                                              "вы можете разъединить с ней соединение")
            markup = types.ReplyKeyboardMarkup(row_width=2)
            next_button = InlineKeyboardButton("Вернуться назад")
            next_button1 = InlineKeyboardButton("Закончить ознакомление")
            markup.add(next_button, next_button1)
            bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
        # Проверка идентификатора
        elif len(text) == 8:
            if text not in crud.get_data(db, message.chat.id):
                crud.create_data(db, message.chat.id, text)
                crud.update_active(db, message.chat.id, text)
                client_pub.publish(text + "/command", "r")
                bot.send_message(message.chat.id, "Ваша подставка подключена")
            else:
                crud.update_active(db, message.chat.id, text)
                bot.send_message(message.chat.id, "Вы можете работать теперь с этой платой")
        # Проверка градусов
        elif len(text) <= 3 and text.isnumeric():
            client_pub.publish(text + "/command", "r")
            bot.send_message(message.chat.id, "Градусы успешно изменены")
        # кнопки
        if text not in ["Изменить градусы", "Сменить плату", "Добавить новую плату", "Как пользоваться?",
                        'Проверка нагревания', 'Проверка охлаждения', 'Смена платы', 'Изменение градусов',
                        'Проверка активности', 'Добавление новой платы', 'Удаление активной подставки',
                        "Вернуться назад"]:
            markup = types.ReplyKeyboardMarkup(row_width=2)
            button_hot = types.InlineKeyboardButton(text='Проверять нагревание')
            button_cold = types.InlineKeyboardButton(text='Проверять охлаждение')
            markup.add(button_hot, button_cold)

            button_change = types.InlineKeyboardButton(text='Сменить плату')
            button_degree = types.InlineKeyboardButton(text='Изменить градусы')
            markup.add(button_change, button_degree)

            button_work = types.InlineKeyboardButton(text='Добавить новую плату')
            button_new = types.InlineKeyboardButton(text='Какая плата сейчас активна?')
            markup.add(button_work, button_new)

            button_how = types.InlineKeyboardButton(text='Как пользоваться?')
            button_removal = types.InlineKeyboardButton(text='Удалить активную подставку')
            markup.add(button_how, button_removal)

            bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("change_board:"))
def handle_change_board_callback(call: CallbackQuery):
    board = call.data.split(":")[1]
    with SessionLocal() as db:
        crud.update_active(db, call.message.chat.id, board)
        bot.send_message(call.message.chat.id, f"Плата {board} теперь активна")


bot.polling()
