from neo4j import GraphDatabase
from dotenv import load_dotenv
from datetime import datetime
import os

load_dotenv()

uri = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USERNAME")
password = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(uri, auth=(username, password))


def get_all_users(tx):
    query = "MATCH (u:User) RETURN u.id AS id, u.name AS name, u.age AS age"
    return list(tx.run(query))


def create_user(id, name, age):
    with driver.session() as session:
        session.execute_write(_create_user_tx, id, name, age)


def _create_user_tx(tx, id, name, age):
    tx.run(
        "MERGE (u:User {id: $id}) SET u.name = $name, u.age = $age",
        id=id,
        name=name,
        age=age,
    )


def create_post(id, content, timestamp):
    with driver.session() as session:
        post_id = f"{id}_{int(datetime.now().timestamp())}"
        session.execute_write(_create_post_tx, id, post_id, content, timestamp)


def _create_post_tx(tx, id: str, post_id: str, content: str, timestamp: str):
    tx.run(
        "MATCH (u:User {id: $id}) CREATE (p:Post {post_id: $post_id, content: $content, timestamp: $timestamp}) MERGE (u)-[:POSTED]->(p)",
        id=id,
        post_id=post_id,
        content=content,
        timestamp=timestamp,
    )


def follow_user(follower_id, followee_id):
    with driver.session() as session:
        session.execute_write(_follow_user_tx, follower_id, followee_id)


def _follow_user_tx(tx, follower_id: str, followee_id: str):
    tx.run(
        "MATCH (a:User {id: $follower_id}), (b:User {id: $followee_id}) MERGE (a)-[:FOLLOWS]->(b)",
        follower_id=follower_id,
        followee_id=followee_id,
    )


def list_followers(id):
    with driver.session() as session:
        return session.execute_read(_list_followers_tx, id)


def _list_followers_tx(tx, id: str):
    result = tx.run(
        "MATCH (f:User)-[:FOLLOWS]->(u:User {id: $id}) RETURN f.id AS follower_id",
        id=id,
    )
    return [record["follower_id"] for record in result]


def comment_on_post(user_id, post_content, comment_content, timestamp):
    with driver.session() as session:
        session.execute_write(_comment_on_post_tx, user_id, post_content, comment_content, timestamp)


def _comment_on_post_tx(tx, user_id, post_content, comment_content):
    tx.run(
        "MATCH (u:User {id: $user_id}), (p:Post {content: $post_content}) CREATE (c:Comment {content: $comment_content, timestamp: $timestamp}) CREATE (u)-[:WROTE]->(c) CREATE (u)-[:COMMENTED_ON]->(p) CREATE (c)-[:ON]->(p)",
        user_id=user_id,
        post_content=post_content,
        comment_content=comment_content,
    )


def main():
    with driver.session() as session:
        users = session.execute_read(get_all_users)
        for user in users:
            print(user)

    usercounter = len(users)

    while True:
        option = input(
            """
Choose a function:
1. Create user
2. Create post
3. Follow user
4. Comment on post
5. List followers of user
6. Get all users
>>> """
        )

        if option == "1":
            name = input("Enter user name: ")
            age = input("Enter user age: ")
            user_id = "user" + str(usercounter + 1)
            create_user(user_id, name, age)
            usercounter += 1
            print(f"User {user_id} created.")

        elif option == "2":
            id = input("Enter user ID: ")
            content = input("Enter post content: ")
            timestamp = datetime.now().isoformat()
            create_post(id, content, timestamp)
            print("Post created.")

        elif option == "3":
            follower_id = input("Enter follower ID: ")
            followee_id = input("Enter followee ID: ")
            follow_user(follower_id, followee_id)
            print("Followed.")

        elif option == "4":
            user_id = input("Enter your user ID: ")
            post_content = input("Enter post content: ")
            comment = input("Enter your comment: ")
            timestamp = datetime.now()
            comment_on_post(user_id, post_content, comment, timestamp)
            print("Comment added.")

        elif option == "5":
            id = input("Enter user ID to list their followers: ")
            followers = list_followers(id)
            print(f"Followers of {id}: {followers}")

        elif option == "6":
            with driver.session() as session:
                users = session.execute_read(get_all_users)
                for user in users:
                    print(user)

        else:
            print("Invalid option. Please choose a valid number.")


if __name__ == "__main__":
    main()
    driver.close()
