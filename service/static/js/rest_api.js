$(function () {

    let selectedWishlistId = null;

    // ******************************************************
    //  U T I L I T Y   F U N C T I O N S FOR WISHLIST
    // ******************************************************

    // Updates the form with data from the response
    function update_form_data(res) {
        $("#wishlist_id").val(res.id);
        $("#wishlist_name").val(res.name);
        $("#wishlist_category").val(res.category);
        $("#wishlist_description").val(res.description);
        $("#wishlist_customer_id").val(res.customer_id);
        $("#wishlist_created_date").val(res.created_date);
        $("#wishlist_updated_date").val(res.updated_date);
    }

    /// Clears all form fields
    function clear_form_data() {
        $("#wishlist_name").val("");
        $("#wishlist_category").val("");
        $("#wishlist_customer_id").val("");
        $("#wishlist_description").val("");
        $("#wishlist_created_date").val("");
        $("#wishlist_updated_date").val("");
    }

    // Updates the flash message area
    function flash_message(message) {
        $("#flash_message").empty();
        $("#flash_message").append(message);
    }

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
    
    // ******************************************************
    //  U T I L I T Y   F U N C T I O N S FOR WISHLIST ITEMS
    // ******************************************************

    function render_items(items) {
        const $tbody = $("#items_results_body");
        $tbody.empty();

        if (!items || items.length === 0) {
            $tbody.append('<tr><td colspan="3" style="opacity:.7;">(No items)</td></tr>');
            return;
        }

        items.forEach((item) => {
            const pid  = item.product_id ?? item.productId ?? item.id ?? "";
            const pos  = item.position   ?? item.rank      ?? "";
            const desc = item.description ?? item.desc     ?? "";

            $tbody.append(`
            <tr>
                <td>${pid}</td>
                <td>${pos}</td>
                <td>${desc}</td>
            </tr>
            `);
        });
    }

    function read_item_inputs() {
        return {
            product_id: $("#item_product_id").val()?.trim(),
            description: $("#item_description").val()?.trim(),
            before_position: $("#item_before_position").val()?.trim(),
        };
    }

    function setSelectedWishlist(id) {
        selectedWishlistId = id ?? null;
        const $panel = $("#items_panel");
        const $controls = $("#search-items-btn, #create-item-btn, #update-item-btn, #delete-item-btn, #move-item-btn, #item_product_id");
        const $tbody = $("#items_results_body");
        const $displayId = $("#item_wishlist_id");

        if (!$panel.length) return;

        if (selectedWishlistId) {
            $panel.show();
            $controls.prop("disabled", false);
            if ($displayId.length) $displayId.val(String(selectedWishlistId));
        } else {
            $panel.hide(); 
            $controls.prop("disabled", true);
            $tbody.empty();
            if ($displayId.length) $displayId.val("");
        }
    }

    function requireSelectedWishlist() {
        if (!selectedWishlistId) {
            flash_message("Please select a wishlist first");
            return false;
        }
        return true;
    }

    // ****************************************
    // Create a Wishlist
    // ****************************************

    $("#create-btn").click(function () {

    });

    // ****************************************
    // Update a Wishlist
    // ****************************************

    $("#update-btn").click(function () {
        
    });


    // ****************************************
    // Retrieve a Wishlist
    // ****************************************

    $("#retrieve-btn").click(function () {

        let wishlist_id = $("#wishlist_id").val();

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
            setSelectedWishlist(res.id)
            flash_message("Success")
        });

        ajax.fail(function(res){
            clear_form_data()
            setSelectedWishlist(null)
            flash_message(res.responseJSON.message)
        });

    });

    // ****************************************
    // Delete a Wishlist
    // ****************************************

    $("#delete-btn").click(function () {
        let wishlist_id = $("#wishlist_id").val();

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
        $("#wishlist_id").val("");
        $("#flash_message").empty();
        clear_form_data();
        setSelectedWishlist(null);
    });

    // ****************************************
    // Search for a Wishlist
    // ****************************************

    $("#search-btn").click(function () {

    });


    // ######################################################################
    // # Wishlist Item
    // ######################################################################

    // ****************************************
    // Create a Wishlist Item
    // ****************************************

    $("#create-item-btn").click(function () {

    });

    // ****************************************
    // Update a Wishlist Item
    // ****************************************

    $("#update-item-btn").click(function () {
        
    });


    // ****************************************
    // Retrieve a Wishlist Item
    // ****************************************

    $("#retrieve-item-btn").click(function () {

    });

    // ****************************************
    // Delete a Wishlist Item
    // ****************************************

    $("#delete-item-btn").click(function () {
    
    });


    // ****************************************
    // Search for a Wishlist Item
    // ****************************************

    $("#search-items-btn").click(function () {

    });


    // ****************************************
    // Move for a Wishlist Item
    // ****************************************

    $("#move-item-btn").click(function () {

    });

})
