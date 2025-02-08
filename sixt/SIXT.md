# SIXT

SIXT SE is a leading international provider of premium mobility services, headquartered in Pullach, Germany. Founded in
1912, the company operates in over 100 countries, offering a range of services including car rental (SIXT rent), car
sharing (SIXT share), ride-hailing (SIXT ride), and car subscriptions (SIXT+). These services are integrated into a
single platform, providing customers with flexible and convenient mobility solutions.

In this system design we focus on the **SIXT share** (car sharing) app design.

## Functional Requirements

1. User should see all closest vehicles on the map.
2. Before renting the car, user should see the price per minute of car renting.
3. Prices are dynamic and depend on demand (we assume price multiplier depending on the predicted traffic in the area),
   number of available cars in the area and location.
4. Once user accepts renting a car no other user is allowed to rend the same car until it is returned.
5. At the end of the road user pays based on time and ride distance.

## System Requirements

1. Target cloud platform is AWS.
2. Ride time and distance must be accurate (for distance it means continuous GPS location tracking).
3. Our main target for AI model: to reach the best accuracy predictions for demand forecasting. This model takes
   location and time as inputs and outputs number of rides for the next 30 minutes (my assumption).
    - System must track where and when the rides were booked.
    - MLOps pipeline must ensure continuous model performance monitoring and improvement.

## Capacity Estimation

1. Everyone in the world takes a 1-hour ride once per week.
2. If a ride is 1-hour long, there are 24 * 7 ~ 200 slots per week.
3. The current world population is 8 billion people => 8 billion / 200 slots = 40 millions rides going on at a time.
4. If we want to track locations of 40 millions cars, it is
   40 millions * (64-bit latitude coordinate + 64-bit longitude coordinates + 64-bit car id) ~ 1 GB.
5. 40 millions rides / 60 minutes ~ 700K requests per minute or 12K requests per second.

## Design Considerations



## Final Design Graph

![sixt.drawio.png](assets/sixt.drawio.png)
