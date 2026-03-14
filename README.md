# Introduction and Project Goals

- This platform provides all the necessary functionality for users to carry out CRUD operations on the back-end.
  Concultations is a E-commerce platform where users can book diffrent types of consultations.
  Every user can see all own booked appointments.
  Users can create accounts to engage in various interactions, such as book new appointment with select date and time, update booking appointment in cart before payment, uploading avatar in profile and saving images to external media store.
- Consultations live link.[Consultations](https://dhiaa-alomari.github.io/consultations-FE).

---

- Consultations back-end. [Heroku-back-end](https://consultations-be-795aeca2a205.herokuapp.com/).
- If you logged in as admin you should see a welcome message otherwise (Authentication credentials were not provided).

---

- front-end GitHub.[Github frond-end](https://github.com/Dhiaa-alomari/consultations-FE).

---

## Table of Contents

- [Project Models](#project-models)
  - [Users](#users)
  - [Consultation Category](#consultationcategory)
  - [Appointment](#appointment)
  - [Cart](#cart)
  - [Cart Item](#cartitem)
  - [Order](#order)
  - [Order Item](#orderitem)
  - [Contact](#contact)
- [Unit Tests](#unit-tests)
- [Postman](#postman)
- [Manual Testing](#manual-testing)
- [Deployment](#deployment)
- [Technologies Used](#technologies-used)
- [Validation](#validation)
- [Bugs](#bugs)
- [Credits](#credits)

---

## Project Models

### Users

| Name       | KYE             | TYPE             | EXTRA                            |
| ---------- | --------------- | ---------------- | -------------------------------- |
| user       | OneToOneField   | User             | on_delete=models.CASCADE, related_name='profile'|
| email      | EmailField      | Email            | unique=True                      |
| phone      | CharField       | String(max=20)   | blank=True                       |
| avatar     | CloudinaryField | Image            | default=DEFAULT_AVATAR, blank=True, null=True |
| bio        | TextField       | Text             | blank=True                       |

### ConsultationCategory

| Name       | KYE           | TYPE                   | EXTRA                                |
| ---------- | ------------- | ---------------------- | ------------------------------------ |
| category   | CharField     | String (max=60)        | choices=CATEGORY_CHOICES, unique=True|
| price_per_15min| DecimalField| Decimal              | max_digits=10, decimal_places=2      |
| description| TextField     | Text                   | blank=True                           |

### Appointment

| Name       | KYE             | TYPE                   | EXTRA                                     |
| ---------- | --------------- | ---------------------- | ----------------------------------------- |
| user       |  ForeignKey     | User                   |on_delete=models.CASCADE, related_name='appointments'|
| category   | ForeignKey      | ConsultationCategory   | on_delete=models.CASCADE, related_name='appointments'|
| date       | DateField       | Date                   | CASCADE, related_name='comments'          |
| time       | TimeField       | Time                   | auto_now_add=True (Set once when created) |
| duration   | IntegerField    | Integer                | choices=DURATION_CHOICES                  |
| total_price| DecimalField    | Decimal                | max_digits=10, decimal_places=2, editable=False, default=0|
| is_paid    | BooleanField    | Boolean                | default=False                             |
| created_at | DateTimeField   | DateTime               | auto_now_add=True                         |

### Cart

| Name       | KYE           | TYPE                   | EXTRA                                     |
| ---------- | ------------- | ---------------------- | ----------------------------------------- |
| user       | OneToOneField | User                   | on_delete=models.CASCADE, related_name='cart'|
| post       | DateTimeField | DateTime               | auto_now_add=True                         |
| created_at | DateTimeField | DateTime               | auto_now=True                             |

### CartItem

| Name           | KYE                  | TYPE                   | EXTRA                                     |
| -------------- | -------------------- | ---------------------- | ----------------------------------------- |
| cart           | ForeignKey           | Cart                   | on_delete=models.CASCADE, related_name='items' |
| category       | ForeignKey           | ConsultationCategory   | on_delete=models.CASCADE |
| date           | DateField            | Date                   |                          |
| time           | TimeField            | Time                   |                          |
| created_at     | DateTimeField        | -                      |                          |
| duration       | IntegerField         | Integer                | choices=DURATION_CHOICES |
| added_at       | DateTimeField        | DateTime               | auto_now_add=True        |

### Order

| Name       | KYE           | TYPE   | EXTRA                                           |
| ---------- | ------------- | ------ | ----------------------------------------------- |
| user       | ForeignKey    | User   | on_delete=models.CASCADE, related_name='orders' |
| total_amount| DecimalField | Decimal| max_digits=10, decimal_places=2                 |
| status     | CharField     | String | choices=STATUS_CHOICES, default='pending'       |
| stripe_payment_intent_id | CharField | String | max_length=255, blank=True            |
| created_at  | DateTimeField| DateTime| auto_now_add=True                              |
| updated_at  | DateTimeField | DateTime | auto_now=True                                |

### OrderItem

| Name       | KYE           | TYPE | EXTRA                                |
| ---------- | ------------- | ---- | ------------------------------------ |
| order      | ForeignKey    | Order| on_delete=models.CASCADE, related_name='items'|
| category   | ForeignKey    | ConsultationCategory| on_delete=models.SET_NULL, null=True|
| category_name| CharField   | String (max=60)| Snapshot name |
| date       | DateField     | Date | on_delete=models.SET_NULL, null=True|
| time       | TimeField     | Time | on_delete=models.CASCADE, related_name='items'|
| duration   | IntegerField  | Integer| choices=DURATION_CHOICES |
| unit_price | DecimalField  | Decimal| max_digits=10, decimal_places=2 |
| total_price| DecimalField  | Decimal| max_digits=10, decimal_places=2 |
| appointment| OneToOneField | Appointment| on_delete=models.SET_NULL, null=True, blank=True|

### Contact

Model inherits fields from AbstractUser
| Name | KYE | TYPE | EXTRA |
| ---------- | ------------- | ---- | -------------------- |
|user| ForeignKey| User | on_delete=models.SET_NULL, null=True, blank=True, related_name='contact_messages'|
|name| CharField| String (max=100) |  |
|email| EmailField| Email |  |
|subject| CharField| String (max=30) |choices=SUBJECT_CHOICES, default='general'|
|message|TextField| Text | |
|created_at|DateTimeField| DateTime|auto_now_add=True|
|is_read|BooleanField| Boolean | default=False|

---

---

## Unit Tests

- Tests for consultations models.
  ![consultation models](/images-readme/test-consultation-models-1.png)
  ![consultation models](/images-readme/test-consultation-models-2.png)
- Creates test instances of categories, appointments.
- Calculate price for different duration (15m, 30m, 60m, 120m).
- Save total price automatically.
- Test double booking same date and time same consultation type.
- Test category choices validation.

---

- Tests for consultations views (APIs).
  ![consultation views](/images-readme/test-consultation-views.png)
- Test public endpoints does not authentication.
- Admin just has permission to manage categories.
- User cannot see profile other users.
- Test paid booking appointments cannot be deleted.
- Test all APIs runs just with authentication.

---

- Tests for consultations serializers (validation).
  ![consultation serializers](/images-readme/test-consultation-serializers-1.png)
  ![consultation serializers](/images-readme/test-consultation-serializers-2.png)
- Reject book an appointment on old date.
- Reject ancorrect duration.
- Could not book appointment before 9am and after 6pm.
- Could not double booking on same date, time and consultation type.
- Test approve to book appointments at same time and date but the type is different.

---

- Tests for users models.
- ![users models](/images-readme/test_user_model.jpg)
- Creates test instances of User.
- Test create user successfully.
- Test email must be unique.
- Test create superuser. 
- Test profile creation manually.
- Test profile fields as defaults and update.
- Test cannot create second profile for same user.

---

- Tests for users views.
- ![users models](/images-readme/test_user_views.jpg)
- هنا لملف test_views.

---
