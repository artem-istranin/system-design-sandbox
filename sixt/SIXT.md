# SIXT

SIXT SE is a leading international provider of premium mobility services, headquartered in Pullach, Germany. Founded in
1912, the company operates in over 100 countries, offering a range of services including car rental (SIXT rent), car
sharing (SIXT share), ride-hailing (SIXT ride), and car subscriptions (SIXT+). These services are integrated into a
single platform, providing customers with flexible and convenient mobility solutions.

In this system design we focus on the **SIXT share** (car sharing) app design.

## Functional Requirements

1. User should see all closest vehicles on the map.
2. Before renting the car, user should see the price per minute of car renting.
3. Prices are dynamic and depend on demand (we assume AI multiplier depending on the predicted traffic in the area),
   number of available cars in the area and location.
4. Once user accepts renting a car no other user is allowed to rend the same car until it is returned.
5. At the end of the road user pays based on time and ride distance.

We focus on this key requirements and can extend it to more requirements over time.

## System Requirements

1. Target cloud platform is AWS.
2. Average ... load XXX. ...
3. Ride time and distance must be accurate (for distance it means continuous GPS location tracking).
4. Our main target for AI model: to reach the best accuracy predictions for demand forecasting. This model takes
   location and time as inputs and outputs number of rides for the next 30 minutes in this
   location.
   - System must track where and when the rides were booked.
   - MLOps pipeline must ensure continuous model performance monitoring and improvement (Continuous Training).

## Design Considerations

### Cars Database

We want to show to the user only relevant cars in some radius quickly after user opens our app.

