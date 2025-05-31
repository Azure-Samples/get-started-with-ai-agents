#!/bin/bash

# Prompt for username and password
# Prompt for username
while true; do
    read -p 'Create a new username for the web app (no spaces, at least 1 character): ' username
    if [[ -z "$username" ]]; then
        echo "Username cannot be empty. Please try again."
    elif [[ "$username" == *" "* ]]; then
        echo "Username cannot contain spaces. Please try again."
    else
        break
    fi
done

# Prompt for password
while true; do
    read -sp 'Create a new password for the web app (no spaces, at least 1 character): ' password
    echo # Ensures the cursor moves to the next line after password input
    if [[ -z "$password" ]]; then
        echo "Password cannot be empty. Please try again."
    elif [[ "$password" == *" "* ]]; then
        echo "Password cannot contain spaces. Please try again."
    else
        break
    fi
done
echo

# Set the environment variables using azd
azd env set WEB_APP_USERNAME $username
azd env set WEB_APP_PASSWORD $password

echo "Username and password have been saved to AZD environment variables."
