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
   ![users models](/images-readme/test_user_model.jpg)
  - Creates test instances of User.
  - Test create user successfully.
  - Test email must be unique.
  - Test create superuser. 
  - Test profile creation manually.
  - Test profile fields as defaults and update.
  - Test cannot create second profile for same user.

---

- Tests for users views.
   ![users views](/images-readme/test_user_views.jpg)
  - Tests for User Registration:
    - Successful Registration: Validates that a new user can successfully register, confirming that the user is created in the database and that the appropriate tokens are generated.
    - Missing Fields: Checks the response when required fields (email, password) are missing during registration.
    - Duplicate Username: Ensures the system prevents registration of a username that already exists.
    - Duplicate Email: Verifies that registration fails when the email is already in use by another user.
  - Tests for User Login:
    - Successful Login with Username: Tests that a user can log in using their username and verifies the returned user details and tokens.
    - Successful Login with Email: Confirms that logging in with the email address works, returning the correct user details.
    - Missing Credentials: Checks the response when login credentials are not provided.
    - Invalid Credentials: Tests that the system denies access when the password is incorrect.
    - Nonexistent UserLogin: Verifies that an error is returned for trying to log in with a username that doesn't exist.
  - Tests for User Logout:
    - Successful Logout: Validates that a user can log out successfully and receives the appropriate confirmation message.
    - Logout without Refresh Token: Checks the system's handling when trying to logout without providing a refresh token.
    - Logout with Invalid Token: Tests logout functionality when an invalid refresh token is supplied.
    - Logout Unauthenticated: Verifies that the system denies logout requests if the user is not authenticated.
  - Tests for User Profile Management:
    - Successful Profile Retrieval: Confirms that authenticated users can successfully retrieve their profiles, checking that the correct details are returned.
    - Profile Access Unauthenticated: Tests the response when a non-authenticated user tries to access a profile.
    - Partial Profile Update: Checks that users can partially update their profile information without affecting other fields.
    - Full Profile Update: Verifies that users can fully update their profile details, ensuring correctness in the database after the update.
    - Partial Update on User Fields Only: Tests that updating only certain user fields (like first name) does not affect other fields.
  - Tests for Password Change:
    - Successful Password Change: Confirms that users can successfully change their passwords.
    - Authenticated Password Change: Verifies that password changes cannot occur without authentication.
    - Wrong Old Password: Checks the error response when the old password is incorrect during a change.
    - Password Mismatch: Ensures the system correctly handles cases where the new password and confirmation do not match.
    - Same as Old Password: Validates that changing to the same password returns an appropriate error.
  - Tests for Account Deletion:
    - Successful Account Deletion: Checks that a user account can be successfully deleted.
    - Account Deletion Unauthenticated: Verifies that account deletion fails when not authenticated.
    - Without Password: Tests the response when a password is not provided during account deletion.
    - Wrong Password for Deletion: Ensures that attempting to delete an account with an incorrect password fails and the account remains intact.

---

- Tests for users serializers.
 ![test users serializers](/images-readme/test_user_serializers.jpg)
  - Register Serializer Tests:
    - Valid Registration Data: Confirms that the serializer validates properly when supplied with all necessary and correct fields during registration.
    - Passwords Must Match: Verifies that an error is raised when the password and password_confirm fields do not match.
    - Email Unique Validation: Tests that the serializer correctly handles cases where the provided email is already taken, ensuring that registration fails.
    - Username Unique Validation: Checks that the serializer prevents registration of a username that already exists in the database.
    - Password Validators Called: Ensures that custom password validation functions are executed when validating a password.
    - Password Uniqueness Check: Validates that the serializer prevents registering a user with a password that is already in use by another user.
    - Create User with Profile: Confirms that registering a user automatically creates an associated profile.
  - Profile Serializer Tests:
    - Profile Serializer Fields: Checks that the profile serializer includes the correct fields (e.g., avatar_url, phone, bio) and excludes any write-only fields.
    - Avatar URL Method: Tests the get_avatar_url method ensures a valid URL is returned when an avatar is present.
    - Avatar URL Without Avatar: Verifies that the get_avatar_url method returns None when no avatar is set for the profile.
  - User Serializer Tests:
    - User Serializer Fields: Validates that the user serializer returns the correct fields (id, username, email, etc.) when serializing a user instance.
    - Read-Only Fields: Ensures that specific fields like id, is_staff, and date_joined are marked as read-only in the serializer.
  - Profile Update Serializer Tests:
    - Update User Fields: Tests that updating the user's fields (e.g., first_name, last_name) works correctly and only modifies the intended fields.
    - Update Profile Fields: Verifies that updating profile fields (e.g., phone, bio) applies changes to the database.
    - Partial Update: Confirms that partial updates (updating only the first name while leaving other fields unchanged) function as expected.
  - Change Password Serializer Tests:
    - Valid Password Change: Ensures that the serializer validates correctly when provided with the appropriate data for changing a password.
    - Old Password Incorrect: Checks for validation failures if the provided old password does not match the user's current password.
    - New Passwords Mismatch: Validates that the serializer raises an error when the new password and its confirmation do not match.
    - New Password Same as Old: Ensures that trying to set a new password that is identical to the old password results in a validation error.
    - Password Uniqueness Check: Confirms that the serializer prevents the user from changing to a password that is already in use by another account.
    - Save Method: Tests the save method of the serializer, verifying that it correctly changes the user's password and updates the database.

---

## Postman

- Tool Used: Postman        
- Base URL: https://consultations-be-795aeca2a205.herokuapp.com
- Authentication: Token-based authentication used for secured endpoints.

- The Postman collection file for this project is located at [postman](https://github.com/Dhiaa-alomari/consultations-BE/blob/main/Consultations-API-Postman-Collection-Test.json) .
- You can import this file into Postman to access the collection of API endpoints and test them.
- Import from postman
- Open Postman.
- Dropdown three dots next to you app name.
- Click on export.
- This will direct you to your computer files where you can choose to locate your postman file.
- By importing the Postman collection, you can seamlessly access and test the API endpoints of the E-PICS Task Management System for functionality.
- I have thoroughly tested all my apps using Postman to ensure that the CRUD operations function correctly.

### Authentication Test by postman:

### Manual Testing
- Base URL: https://consultations-be-795aeca2a205.herokuapp.com
---
- User Registration
  - Endpoint: POST /api/auth/register/
    - Case: Normal reisteration.
    ![postman test](/images-readme/register_good_case.png)
    - Case: cannot duplicate email with two users account.
    ![postman test](/images-readme/register_cannot_duplicate_email_with_two_accounts.png)
    - Case: confirmed password does not match password.
    ![postman test](/images-readme/register_error_case_dont_pw_match.png)
    ![postman test](/images-readme/register_error_case_response_dont_pw_match.png)
    - Case: the password must be at least 8 characters.
    ![postman test](/images-readme/register_error_case_pw_8_char.png)
- User Login
  - Endpoint: POST /api/auth/login/
    - Case: Normal log in.
    ![postman test](/images-readme/login_correct_data.png)
    - Case: log in by email, not by username.
    ![postman test](/images-readme/login_by_email.png)
    - Case: log in with incorrect password.
    ![postman test](/images-readme/login_erroe_case_incorrect_password.png)
- User token
  - Endpoint: POST /api/auth/token/refresh/
    - Case: get a new refresh token.
    ![postman test](/images-readme/refresh_token.png)
- User log out
  - Endpoint: POST /api/auth/logout/
    - Case: Normal log out, correct token must be existing on header.
    ![postman test](/images-readme/logout.png)
- User Change Password
  - Endpoint: POST /api/auth/change-password/
    - Case: Normal change password, correct token must be existing on header.
    ![postman test](/images-readme/change_password_good_case.png)
    - Case: weak password not acceptable, must include letters and numbers, correct token must be existing on header.
    ![postman test](/images-readme/change_password_error_case_pw_weak_just_numbers.png)
    - Case: use incorrect current password when change password, correct token must be existing on header.
    ![postman test](/images-readme/change_password_error_case_incorrect_pw.png)
    deleter_account_good_case
- User Delete Account
  - Endpoint: DELETE /api/auth/delete-account/
    - Case: Normal delete account, password is required, correct token must be existing on header.
    ![postman test](/images-readme/deleter_account_good_case.png)
    - Case: enter incorrect password, correct token must be existing on header.
    ![postman test](/images-readme/deleter_account_error_case_incorrect_pw.png)
    ![postman test](/images-readme/deleter_account_error_case_incorrect_pw_CODE.png)
    - Case: ignore enter password for removing account, correct token must be existing on header.
    ![postman test](/images-readme/deleter_account_error_case_pw_required.png)
    ![postman test](/images-readme/deleter_account_error_case_pw_required_CODE.png)
  - Endpoint: POST /api/auth/login/
    - Case: log in by removed account.
    ![postman test](/images-readme/deleter_account_unavailable_account_now.png)
- User Profile
  - Endpoint: GET /api/auth/profile/
    - Case: Normal get profile, correct token must be existing on header.
    ![postman test](/images-readme/get_profile.png)
  - Endpoint: PATCH /api/auth/profile/
    - Case: update profile details, set data in (form) body, correct token must be existing on header.
    ![postman test](/images-readme/profile_upload_new_image_to_cloud.png)
- Categories
  - Endpoint: GET /api/consultations/categories/
    - Case: Normal get all available categorioes.
    ![postman test](/images-readme/category_get_all_categories.png)
  - Endpoint: PATCH /api/consultations/categories/1/
    - Case: update specific category, data in body, login with admin account is required.
    ![postman test](/images-readme/category_update_specific_category_price.png)
- Contact
  - Endpoint: GET /api/contact/messages/
    - Case: Normal get all messages, __required:__ admin is logged in.
    ![postman test](/images-readme/contact_show_all_messages_by_admin.png)
    - Case: try normal user to get all messages.
    ![postman test](/images-readme/contact_error_case_try_show_messages_by_user.png)
  - Endpoint: POST /api/contact/
    - Case: Normal send message without login.
    ![postman test](/images-readme/contact_send_message.png)
    ![postman test](/images-readme/contact_send_message_while_NOT_logged_in.png)
    - Case: Normal send message with login, existing token on header.
    ![postman test](/images-readme/contact_send_message_while_logged_in.png)
    - Case: body message too short.
    ![postman test](/images-readme/contact_error_case_msg_too_short.png)
    - Case: sender name does not enter.
    ![postman test](/images-readme/contact_error_case_name_empty.png)
- Appointments
  - Endpoint: POST /api/consultations/appointments/
    - Case: Normal create a new appointment, existing token is required on header.
    ![postman test](/images-readme/appointment_create_new.png)
  - Endpoint: GET /api/consultations/availability/?category=3data=20260301
    - Case: Normal check if the date is in future and category is available in database.
    ![postman test](/images-readme/appointment_check_slot_availabilty_available.png)
  - Endpoint: POST /api/orders/cart/
    - Case: try to book on past date.
    ![postman test](/images-readme/appointment_book_appointments_on_pastDate.png)
  - Endpoint: POST /api/consultations/appointments/
    - Case: create a new appointment but the date, time and category reserved by other appointment.
    ![postman test](/images-readme/appointment_error_case_create_duplicate.png)
  - Endpoint: GET /api/consultations/my-appointments/
    - Case: get all reserved appointments by the user, existing token on header.
    ![postman test](/images-readme/appointment_get_UserAppointments_history.png)

    cart_add_more_appointments
- Cart
  - Endpoint: POST /api/orders/cart/
    - Case: Normal add more appointment to the cart, existing token is required on header.
    ![postman test](/images-readme/cart_add_more_appointments.png)
  - Endpoint: DELETE /api/orders/cart/items/2/
    - Case: Normal remove item from the cart, existing token is required on header.
    ![postman test](/images-readme/cart_remove_item_in_cart.png)
  - Endpoint: PATCH /api/orders/cart/items/2/
    - Case: Normal update item from the cart, body is required, existing token is required on header.
    ![postman test](/images-readme/cart_update_item_in_cart.png)
  - Endpoint: DELETE /api/orders/cart/clear/
    - Case: clear the cart, existing token is required on header.
    ![postman test](/images-readme/cart_clear_cart.png)
- Checkout
  - Endpoint: POST /api/orders/checkout/
    - Case: Normal payment by Strip, existing token is required on header.
    ![postman test](/images-readme/checkout_with_stripe.png)
- Orders
  - Endpoint: GET /api/orders/
    - Case: Normal get all user's orders, existing token is required on header.
    ![postman test](/images-readme/order_show_all_orders.png)
  - Endpoint: GET /api/orders/1/
    - Case: Normal get specific order, existing token is required on header.
    ![postman test](/images-readme/order_show_specific_order_details.png)
---

## Deployment

- Local Deployment

1. Clone the git repository
2. Navigate into your local project folder
3. pip Install
4. Install the dependencies with < pip install -r requirements.txt.>
5. Create a local env.py file and set the following environment variables inside it:
   - ALLOWED_HOST
   - CLIENT_ORIGIN
   - CLIENT_ORIGIN_DEV
   - DATABASE_URL
   - SECRET_KEY
   - CSRF_TRUSTED_ORIGINS
   - CORS_ALLOWED_ORIGIN_REGEX
   - CSRF_TRUSTED_ORIGINS
   - CLOUDINARY_URL
6. Command to run the project loacaly < python manage.py runserver>

- The project is deployed on Heroku using Heroku PostgreSQL as the database

1. Create a Heroku account.
2. Log in to Heroku CLI (heroku login) and create a new Heroku app (heroku create).
3. Setting: Set up Heroku PostgreSQL as the database and other global variables you have in env.py file (in settings Config Vars).
4. Deploy: Connect Github Repository to the app you just create it.
5. Deploy: Deploy Branch.
6. Your App application should now be deployed and accessible via the provided Heroku app URL.

---

## Technologies Used

- **Core Technologies**
  - Python – Main programming language.
  - Django (v5.1.4) – Web framework for building the backend.
  - Django REST Framework (DRF) Used for building REST APIs.
- **Authentication & Security**
  - dj-rest-auth – Provides authentication endpoints.
  - django-allauth – Handles social authentication.
  - django-cors-headers – Manages CORS policies.
- **Database & ORM**
  - PostgreSQL – Database management system.
  - dj-database-url (v0.5.0) – Database configuration tool.
  - psycopg2-binary (v2.9.10) – PostgreSQL adapter for Django.
  - sqlparse – SQL query parsing.
- **Cloud & Storage**
  - Cloudinary (v1.41.0) – Cloud-based media storage.
  - django-cloudinary-storage (v0.3.0) – Cloudinary integration for Django.
  - pillow (v11.0.0) – Image processing library.
- **Deployment & Server**
  - Gunicorn (v23.0.0) – WSGI HTTP server for running the application.
  - Whitenoise (v6.8.2) – Serves static files efficiently.
  - Heroku – Cloud platform for deployment.
- **Utilities & Other Dependencies**
  - asgiref (v3.8.1) – ASGI compatibility for Django.
  - pillow (v11.0.0) – Image processing library.
  - python-decouple (v3.8) – Handles environment variables.
  - requests-oauthlib (v2.0.0) – OAuth authentication.
  - tzdata (v2024.2) – Timezone management.
  - pytz (v2024.2) – Timezone utilities.

## Validation

- I used [PEP8 CI Python linter](https://pep8ci.herokuapp.com/) validation to all my files, and Results:
  All clear, no errors found.

---

## Bugs

- Heroku ask about static files like css, js, html and images but in this project static files found in the frontend project.
- Error with whitenoise middleware:
- ![os](/images-readme/whitenoise-error-test-all-files.png)
- Fixed, error solved by change compression type that used by whitenoise then whitenoise ignore static folder if it is empty:
- ![os](/images-readme/whitenoise-fixed-test-all-files.png)
- ![os](/images-readme/whitenoise-fixed-test-all-files_2.png)

---

- Error occured because of < os > was not imported.
- ![os](/images-readme/os_not_imported.jpg)

---

## Credits

- I would like to express my sincere gratitude to Code Institute for providing me with the education and guidance needed to complete this project. I am especially thankful for their understanding and support in granting me extra time to work on the project during my health-related challenges. Their compassion and flexibility truly made a difference in helping me reach this milestone.
- Thanks to Code Institute Slack Community and Stack Overflow for problem-solving support.
