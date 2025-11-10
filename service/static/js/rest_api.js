$(function () {

    // ****************************************
    //  U T I L I T Y   F U N C T I O N S
    // ****************************************

    // Updates the form with data from the response
    function update_form_data(res) {
        $("#id").val(res.id);
        $("#customer_id").val(res.customer_id);
        $("#name").val(res.name);
        $("#description").val(res.description);
        $("#category").val(res.category);
    }

    /// Clears all form fields
    function clear_form_data() {
        $("#id").val("");
        $("#customer_id").val("");
        $("#name").val("");
        $("#description").val("");
        $("#category").val("");
    }

    // Updates the flash message area
    function flash_message(message) {
        $("#flash_message").empty();
        $("#flash_message").append(message);
    }

    // ****************************************
    // Create a Wishlist
    // ****************************************

    $("#create-btn").click(function () {

        let customer_id = $("#customer_id").val();
        let name = $("#name").val();
        let description = $("#description").val();
        let category = $("#category").val();

        let data = {
            "customer_id": parseInt(customer_id),
            "name": name,
            "description": description,
            "category": category
        };

        $("#flash_message").empty();
        
        let ajax = $.ajax({
            type: "POST",
            url: "/wishlists",
            contentType: "application/json",
            data: JSON.stringify(data),
        });

        ajax.done(function(res){
            update_form_data(res)
            flash_message("Success")
        });

        ajax.fail(function(res){
            flash_message(res.responseJSON.message)
        });

    });


    // ****************************************
    // Update a Wishlist
    // ****************************************

    $("#update-btn").click(function () {

        let wishlist_id = $("#id").val();
        let customer_id = $("#customer_id").val();
        let name = $("#name").val();
        let description = $("#description").val();
        let category = $("#category").val();

        let data = {
            "customer_id": parseInt(customer_id),
            "name": name,
            "description": description,
            "category": category
        };

        $("#flash_message").empty();

        let ajax = $.ajax({
                type: "PUT",
                url: `/wishlists/${wishlist_id}`,
                contentType: "application/json",
                data: JSON.stringify(data)
            })

        ajax.done(function(res){
            update_form_data(res)
            flash_message("Success")
        });

        ajax.fail(function(res){
            flash_message(res.responseJSON.message)
        });

    });

    // ****************************************
    // Retrieve a Wishlist
    // ****************************************

    $("#retrieve-btn").click(function () {

        let wishlist_id = $("#id").val();

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "GET",
            url: `/wishlists/${wishlist_id}`,
            contentType: "application/json",
            data: ''
        })

        ajax.done(function(res){
            //alert(res.toSource())
            update_form_data(res)
            flash_message("Success")
        });

        ajax.fail(function(res){
            clear_form_data()
            flash_message(res.responseJSON.message)
        });

    });

    // ****************************************
    // Delete a Wishlist
    // ****************************************

    $("#delete-btn").click(function () {

        let wishlist_id = $("#id").val();

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "DELETE",
            url: `/wishlists/${wishlist_id}`,
            contentType: "application/json",
            data: '',
        })

        ajax.done(function(res){
            clear_form_data()
            flash_message("Wishlist has been Deleted!")
        });

        ajax.fail(function(res){
            flash_message("Server error!")
        });
    });

    // ****************************************
    // Clear the form
    // ****************************************

    $("#clear-btn").click(function () {
        $("#id").val("");
        $("#flash_message").empty();
        clear_form_data()
    });

    // ****************************************
    // Search for a Wishlist
    // ****************************************

    $("#search-btn").click(function () {

        let customer_id = $("#customer_id").val();
        let name = $("#name").val();
        let category = $("#category").val();

        console.log("DEBUG: Search clicked");
        console.log("DEBUG: customer_id=", customer_id, "name=", name, "category=", category);

        let queryString = ""

        if (customer_id) {
            queryString += 'customer_id=' + customer_id
        }
        if (name) {
            if (queryString.length > 0) {
                queryString += '&name=' + name
            } else {
                queryString += 'name=' + name
            }
        }
        if (category) {
            if (queryString.length > 0) {
                queryString += '&category=' + category
            } else {
                queryString += 'category=' + category
            }
        }

        console.log("DEBUG: Query string:", queryString);
        console.log("DEBUG: Request URL:", `/wishlists?${queryString}`);

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "GET",
            url: `/wishlists?${queryString}`,
            contentType: "application/json",
            data: ''
        })

        ajax.done(function(res){
            console.log("DEBUG: Search SUCCESS");
            console.log("DEBUG: Response:", res);
            console.log("DEBUG: Number of results:", res.length);
            
            $("#search_results").empty();
            console.log("DEBUG: search_results cleared");
            
            let table = '<table class="table table-striped" cellpadding="10">'
            table += '<thead><tr>'
            table += '<th class="col-md-2">ID</th>'
            table += '<th class="col-md-2">Customer ID</th>'
            table += '<th class="col-md-2">Name</th>'
            table += '<th class="col-md-2">Description</th>'
            table += '<th class="col-md-2">Category</th>'
            table += '</tr></thead><tbody>'
            
            let firstWishlist = "";
            for(let i = 0; i < res.length; i++) {
                let wishlist = res[i];
                console.log("DEBUG: Adding row", i, ":", wishlist);
                table +=  `<tr id="row_${i}"><td>${wishlist.id}</td><td>${wishlist.customer_id}</td><td>${wishlist.name}</td><td>${wishlist.description}</td><td>${wishlist.category}</td></tr>`;
                if (i == 0) {
                    firstWishlist = wishlist;
                }
            }
            table += '</tbody></table>';
            
            console.log("DEBUG: Table HTML length:", table.length);
            console.log("DEBUG: Table HTML preview:", table.substring(0, 200));
            
            $("#search_results").append(table);
            console.log("DEBUG: Table appended to #search_results");
            
            let resultHTML = $("#search_results").html();
            console.log("DEBUG: search_results content length:", resultHTML.length);
            console.log("DEBUG: search_results preview:", resultHTML.substring(0, 200));

            // copy the first result to the form
            if (firstWishlist != "") {
                update_form_data(firstWishlist)
                console.log("DEBUG: First wishlist copied to form");
            }

            flash_message("Success")
            console.log("DEBUG: Flash message set to Success");
        });

        ajax.fail(function(res){
            console.error("DEBUG: Search FAILED");
            console.error("DEBUG: Error response:", res);
            flash_message(res.responseJSON.message)
        });

    });

    $("#list-btn").click(function () {

        console.log("DEBUG: List all clicked");

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "GET",
            url: `/wishlists`,
            contentType: "application/json",
            data: ''
        })

        ajax.done(function(res){
            console.log("DEBUG: List all SUCCESS");
            console.log("DEBUG: Response:", res);
            console.log("DEBUG: Number of results:", res.length);
            
            $("#search_results").empty();
            console.log("DEBUG: search_results cleared");
            
            let table = '<table class="table table-striped" cellpadding="10">'
            table += '<thead><tr>'
            table += '<th class="col-md-2">ID</th>'
            table += '<th class="col-md-2">Customer ID</th>'
            table += '<th class="col-md-2">Name</th>'
            table += '<th class="col-md-2">Description</th>'
            table += '<th class="col-md-2">Category</th>'
            table += '</tr></thead><tbody>'
            
            let firstWishlist = "";
            for(let i = 0; i < res.length; i++) {
                let wishlist = res[i];
                console.log("DEBUG: Adding row", i, ":", wishlist);
                table +=  `<tr id="row_${i}"><td>${wishlist.id}</td><td>${wishlist.customer_id}</td><td>${wishlist.name}</td><td>${wishlist.description}</td><td>${wishlist.category}</td></tr>`;
                if (i == 0) {
                    firstWishlist = wishlist;
                }
            }
            table += '</tbody></table>';
            
            console.log("DEBUG: Table HTML length:", table.length);
            
            $("#search_results").append(table);
            console.log("DEBUG: Table appended to #search_results");

            // copy the first result to the form
            if (firstWishlist != "") {
                update_form_data(firstWishlist)
                console.log("DEBUG: First wishlist copied to form");
            }

            flash_message("Success")
            console.log("DEBUG: Flash message set to Success");
        });

        ajax.fail(function(res){
            console.error("DEBUG: List all FAILED");
            console.error("DEBUG: Error response:", res);
            flash_message(res.responseJSON.message)
        });

    });
})

