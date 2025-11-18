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
    Then I should see "Wishlists RESTful Service" in the title
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

Scenario: Create a Wishlist with missing data
    When I visit the "Home Page"
    And I set the "Name" to "Test Wishlist"
    And I press the "Create" button
    Then I should see the message "customer_id"

Scenario: List all wishlists
    When I visit the "Home Page"
    And I press the "List" button
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
    Then I should see the message "Wishlist has been Updated!"
    

Scenario: Delete a Wishlist by ID
    When I visit the "Home Page"
    And I set the "Name" to "Electronics"
    And I press the "Search" button
    Then I should see the message "Success"
    When I press the "Delete" button
    Then I should see the message "Wishlist has been Deleted!"
    When I press the "Clear" button
    And I set the "Name" to "Electronics"
    And I press the "Search" button
    Then I should see the message "Success"
    And I should not see "Electronics" in the results

Scenario: Retrieve a wishlist item

Scenario: Create a Wishlist Item for an existing wishlist
    When I visit the "Home Page"
    And I set the "Name" to "Books"
    And I press the "Search" button
    Then I should see the message "Success"
    And I should see "Books" in the results
    When I set the "Item ID" to "888"
    And I set the "Item Description" to "Database Systems"
    And I press the "Create Item" button
    Then I should see the message "Item added successfully"
    When I set the "Item ID" to "888"
    And I press the "Retrieve Item" button
    Then I should see the message "Item retrieved successfully"
    And I should see "888" in the "Item ID" field
    And I should see "Database Systems" in the "Item Description" field
    When I set the "Item ID" to "777"
    And I set the "Item Description" to "C Programming Language"
    And I press the "Create Item" button
    Then I should see the message "Item added successfully"
    And I should see "777" in the items results
    And I should see "C Programming Language" in the items results

Scenario: Search wishlist items for an existing wishlist
    When I visit the "Home Page"
    And I set the "Name" to "Books"
    And I press the "Search" button
    Then I should see the message "Success"
    And I should see "Books" in the results
    When I set the "Item ID" to "888"
    And I set the "Item Description" to "Operating Systems"
    And I press the "Create Item" button
    Then I should see the message "Item added successfully"
    When I press the "Search Items" button
    Then I should see "888" in the items results
    And I should see "Operating Systems" in the items results

Scenario: Move a wishlist item to a different position
    When I visit the "Home Page"
    And I set the "Name" to "Books"
    And I press the "Search" button
    Then I should see the message "Success"
    When I set the "Item ID" to "111"
    And I set the "Item Description" to "First Book"
    And I press the "Create Item" button
    Then I should see the message "Item added successfully"
    When I set the "Item ID" to "222"
    And I set the "Item Description" to "Second Book"
    And I press the "Create Item" button
    Then I should see the message "Item added successfully"
    When I press the "Search Items" button
    Then I should see "111" in the items results
    And I should see "222" in the items results
    When I set the "Item ID" to "222"
    And I set the "Item Before Position" to "1"
    And I press the "Move Item" button
    Then I should see the message "Item reordered successfully"
    When I press the "Search Items" button
    Then I should see "222" before "111" in the ordered items results

Scenario: Delete a wishlist item
    When I visit the "Home Page"
    And I set the "Name" to "Books"
    And I press the "Search" button
    Then I should see the message "Success"
    And I should see "Books" in the results
    When I set the "Item ID" to "999"
    And I set the "Item Description" to "Book to be deleted"
    And I press the "Create Item" button
    Then I should see the message "Item added successfully"
    And I should see "999" in the items results
    When I set the "Item ID" to "999"
    And I press the "Delete Item" button
    Then I should see the message "Item deleted successfully"
    When I press the "Search Items" button
    Then I should not see "999" in the items results

Scenario: Update a wishlist item description
    When I visit the "Home Page"
    And I set the "Name" to "Books"
    And I press the "Search" button
    Then I should see the message "Success"
    And I should see "Books" in the results
    When I set the "Item ID" to "555"
    And I set the "Item Description" to "Original Description"
    And I press the "Create Item" button
    Then I should see the message "Item added successfully"
    And I should see "555" in the items results
    And I should see "Original Description" in the items results
    When I set the "Item ID" to "555"
    And I set the "Item Description" to "Updated Description"
    And I press the "Update Item" button
    Then I should see the message "Item updated successfully"
    When I press the "Search Items" button
    Then I should see "555" in the items results
    And I should see "Updated Description" in the items results
    And I should not see "Original Description" in the items results


