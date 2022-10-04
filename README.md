
Backend API for a web app imitating booking.com. Instead of being a platform for various places this app is designed to be website of a holiday house renting company with 3 houses in total.


![](2022-10-04-11-22-58.png)

Implemented CustomUserModel where user is depicted by a MyCustomUser model which in turn is linked with CustomerProfile where data such as number of visits is stored. User is not aware of the CustomerProfile model -> it stays in the background for statistics purposes.

CustomerProfile sets up a customer hierarchy (New customer, regular, super) which at the moment does not have a particular function apart from minor things like no/less restrictive throttle.
________________
User are allowed to post opinions only if logged in or if the name and surname provided by them (not authenticated) matches with a name, surname of a user/customer who visited houses in the past (total_vists > 0).

Everyone can send a suggestion (neighbours etc, users without any visits etc.)

_______________
Chalet House view provides a list with already reserved dates:

![](2022-10-04-11-23-32.png)

but also a list with free dates

![](2022-10-04-11-24-17.png)

view can be filtered out/shrunk to just one house. Both above lists are computed based on the reservations and their start_end_dates when page is run.

Detail view, additionally, provides users  with their reservations (admins see all for a given house)

_______________

Reservation is the main point of the app. Linked with customerprofile/user and house. It has a "confirmation system" where a reservation might be:
1. Confirmed .2 Not Confirmed 3.Cancelled 4. Completed

Cancellation cannot be reverted. By default reservation is not confirmed and confirmation is not required but welcome. Completion status is changed automatically via celery periodic task which runs every 30 min (although can be adjusted easily).

Creation of reservation is inherently connected with a pdf confirmation which is generated automatically and sent over to the user email
(Status changes trigger email send with new statys as well -> celery share task)

Reservations views split them between current/future and past reservations. Reservation is marked as pased if the end_date is past today (celery periodic task)
The same task updates customer profile with number of visits.


___________

Endpoint "run_updates" is a function which does essentialy the same as the periodic task... runs updates on reservations/customer_profiles but can be triggered by admin. It was a pre-celery version of the program.

________

Stats provides a nice extract of various statistics related to all models mentioned above.


