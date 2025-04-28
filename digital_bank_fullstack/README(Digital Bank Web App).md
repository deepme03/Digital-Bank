# Digital Bank MVP - Setup and Run Instructions

## Prerequisites

Before you begin, make sure you have the following installed on your system:

-   **Node.js:** (version 12 or higher) - [Download Node.js](https://nodejs.org/en/download/)
-   **npm:** (usually comes with Node.js)
-   **PostgreSQL:** (version 12 or higher) - [Download PostgreSQL](https://www.postgresql.org/download/)
-   **Git:** (if you want to clone the repository) - [Download Git](https://git-scm.com/downloads)

## Installation

1.  **Clone the repository (optional):**

    If you have the project files in a Git repository (e.g., on GitHub), clone it to your local machine:

    ```bash
    git clone <your_repository_url>
    cd <your_project_directory>
    ```

2.  **Navigate to the project directory:**

    If you downloaded the project files as a ZIP archive or already have them locally, navigate to the project's root directory in your terminal:

    ```bash
    cd <your_project_directory>
    ```

3.  **Set up the PostgreSQL database:**

    -   **Start PostgreSQL:** Start the PostgreSQL server on your local machine.
    -   **Create a database:** You can use the PostgreSQL command-line tools (psql) or a GUI like pgAdmin to create a new database.  For example, using psql:

        ```bash
        sudo -u postgres psql
        CREATE DATABASE your_database_name;
        CREATE USER your_database_user WITH PASSWORD 'your_database_password';
        GRANT ALL PRIVILEGES ON DATABASE your_database_name TO your_database_user;
        \q
        ```

        Replace  `your_database_name`,  `your_database_user`, and  `your_database_password`  with your desired values.  **Important:** Store these credentials securely; you'll need them in the next step.
    -   **Create the database schema:**
        -   Navigate to the project directory where the `schema.sql` file is located.
        -   Use `psql` to connect to your database and execute the schema:
        ```bash
        psql -U your_database_user -d your_database_name -f schema.sql
        ```
        You'll be prompted to enter the password you set for your database user.

4.  **Configure the application:**

    -   Create a `.env` file in the project's root directory.
    -   Add the following environment variables to the `.env` file, replacing the values with your PostgreSQL credentials:

        ```
        DATABASE_HOST=your_database_host
        DATABASE_PORT=5432
        DATABASE_NAME=your_database_name
        DATABASE_USER=your_database_user
        DATABASE_PASSWORD=your_database_password
        SECRET_KEY=your_secret_key # Add a secret key for your application
        ```

        * `your_database_host`:  Usually  `localhost`  if PostgreSQL is running on your machine.
        * `your_database_name`:  The name of the database you created in the previous step.
        * `your_database_user`:  The username you created for the database.
        * `your_database_password`:  The password for the database user.
        * `your_secret_key`:  A secret key used for session management.  Choose a strong, random value.

5.  **Install backend dependencies:**

    Navigate to the backend directory and install the necessary Node.js packages:

    ```bash
    npm install
    ```

6.  **Install frontend dependencies and build the front end:**
     Navigate to the frontend directory, install the dependencies, and build the React application:
    ```bash
    cd frontend
    npm install
    npm run build
    cd ..
    ```

7.  **Run the application:**

    Start the Node.js server:

    ```bash
    npm start
    ```

    The server will start, and you can access the application in your web browser at `http://localhost:5000`.
