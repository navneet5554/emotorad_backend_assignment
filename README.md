# emotorad_backend_assignment
Repo for backend assignment tasks

**########################
run below commands step by step for Task-1 :**

 $docker-compose up -d --build (to build docker image and bring up all docker container)
  
  $docker exec -it mongo1 bash
 
  $mongosh -u admin -p adminpassword --authenticationDatabase admin
  rs.initiate({_id: "rs0",members: [{ _id: 0, host: "mongo1:27017" },{ _id: 1, host: "mongo2:27017" },{ _id: 2, host: "mongo3:27017" },]})
  (above commands are used to login into mongo1 docker container and initialize replicaset)

**  ##First we will insert data into database**
  
$curl -X POST -H "Content-Type: application/json" -d '{"email": "test@example.com", "phoneNumber": "1234567890"}' http://localhost:5000/identify

**##now running below command will insert this data as parimary contact and convert previos entry as secondary and prints both contact ids, unique email and phone number
**

$curl -X POST -H "Content-Type: application/json" -d '{"email": "test@example.com", "phoneNumber": "1111111111"}' http://localhost:5000/identify

**###if you want to see all the database item then run below command
**

$curl localhost:5000/all


##################################################

**###run below commands step by step for Task-2 :
**
##follow below steps to run MQTT and Redis server container

$ git clone <repo-url>

$ cd task-2

$ docker compose up
