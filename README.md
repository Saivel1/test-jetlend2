# Orders

Django-проект для создания заказов с поддержкой промокодов.

## Стек

- Python 3.10+
- Django 4.2+
- Django REST Framework
- SQLite

## Установка
```bash
git clone https://github.com/Saivel1/test-jetlend2
cd orders
uv sync
```

## Запуск
```bash
python manage.py migrate
python manage.py runserver
```

## API

### Создать заказ

**POST** `/api/orders/`
```json
{
  "user_id": 1,
  "items": [
    {"product_id": 1, "quantity": 2}
  ],
  "promocode": "SAVE10"
}
```

**Ответ 201:**
```json
{
  "id": 1,
  "user_id": 1,
  "promocode": "SAVE10",
  "total_price": "1000.00",
  "discounted_price": "900.00",
  "created_at": "2026-04-03T10:00:00Z",
  "items": [
    {"product_id": 1, "product_name": "Laptop", "quantity": 2, "price": "500.00"}
  ]
}
```

## Правила применения промокода

- Промокод должен существовать в БД
- Не должен быть просрочен
- Не должен превышать лимит использований
- Один пользователь не может использовать промокод дважды
- Если промокод ограничен категорией — скидка только на товары этой категории
- Товары с `is_promo_excluded=True` не участвуют в акциях

## Тесты
```bash
python manage.py test apps.orders.tests
```
