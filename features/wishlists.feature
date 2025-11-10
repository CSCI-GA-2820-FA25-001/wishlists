Feature: The wishlist service back-end
    As a Wishlist Service Owner
    I need a RESTful wishlist service
    So that I can keep track of all customer wishlists

Background:
    Given the following wishlists
        | customer_id | name           | description              | category    |
        | 1001        | Birthday Gifts | Items for my birthday    | gifts       |
        | 1001        | Holiday        | Christmas wishlist       | holiday     |
        | 1002        | Books          | My reading list          | books       |
        | 1001        | Electronics    | Electronics I want       | electronics |


Scenario: The server is running
    When I visit the "Home Page"
    Then I should see "Wishlist RESTful Service" in the title
    And I should not see "404 Not Found"

Scenario: Create a Wishlist
    When I visit the "Home Page"
    And I set the "Customer ID" to "1003"
    And I set the "Name" to "Summer Vacation"
    And I set the "Description" to "Items for summer trip"
    And I set the "Category" to "travel"
    And I press the "Create" button
    Then I should see the message "Success"
    When I copy the "Name" field
    And I press the "Clear" button
    Then the "Customer ID" field should be empty
    And the "Name" field should be empty
    And the "Description" field should be empty
    And the "Category" field should be empty

Scenario: List all wishlists
    When I visit the "Home Page"
    And I press the "Search" button
    Then I should see the message "Success"
    And I should see "Birthday Gifts" in the results
    And I should see "Holiday" in the results
    And I should see "Books" in the results
    And I should see "Electronics" in the results

Scenario: Search wishlists by customer ID
    When I visit the "Home Page"
    And I set the "Customer ID" to "1001"
    And I press the "Search" button
    Then I should see the message "Success"
    And I should see "Birthday Gifts" in the results
    And I should see "Holiday" in the results
    And I should see "Electronics" in the results
    And I should not see "Books" in the results

Scenario: Search wishlists by category
    When I visit the "Home Page"
    And I set the "Category" to "gifts"
    And I press the "Search" button
    Then I should see the message "Success"
    And I should see "Birthday Gifts" in the results
    And I should not see "Holiday" in the results
    And I should not see "Books" in the results
    And I should not see "Electronics" in the results

Scenario: Search wishlists by name (partial match)
    When I visit the "Home Page"
    And I set the "Customer ID" to "1001"
    And I set the "Name" to "Gift"
    And I press the "Search" button
    Then I should see the message "Success"
    And I should see "Birthday Gifts" in the results
    And I should not see "Holiday" in the results

Scenario: Update a Wishlist
    When I visit the "Home Page"
    And I set the "Name" to "Birthday Gifts"
    And I press the "Search" button
    Then I should see the message "Success"
    And I should see "Birthday Gifts" in the "Name" field
    And I should see "Items for my birthday" in the "Description" field
    When I change "Name" to "Birthday Wishlist"
    And I change "Description" to "Updated birthday list"
    And I press the "Update" button
    Then I should see the message "Success"
    When I copy the "Name" field
    And I press the "Clear" button
    And I paste the "Name" field
    And I press the "Retrieve" button
    Then I should see the message "Success"
    And I should see "Birthday Wishlist" in the "Name" field
    And I should see "Updated birthday list" in the "Description" field
    When I press the "Clear" button
    And I press the "Search" button
    Then I should see the message "Success"
    And I should see "Birthday Wishlist" in the results
    And I should not see "Birthday Gifts" in the results

Scenario: Delete a Wishlist
    When I visit the "Home Page"
    And I set the "Name" to "Electronics"
    And I press the "Search" button
    Then I should see the message "Success"
    When I copy the "Name" field
    And I press the "Clear" button
    And I paste the "Name" field
    And I press the "Delete" button
    Then I should see the message "Success"
    When I press the "Clear" button
    And I press the "Search" button
    Then I should see the message "Success"
    And I should not see "Electronics" in the results