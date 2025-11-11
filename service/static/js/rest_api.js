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
        let name = $("#wishlist_name").val();
        let category = $("#wishlist_category").val();
        let customer_id = $("#wishlist_customer_id").val();

        let queryString = "";
        if (name) {
            queryString += 'name=' + name;
        }
        if (category) {
            if (queryString.length > 0) {
                queryString += '&category=' + category;
            } else {
                queryString += 'category=' + category;
            }
        }
        if (customer_id) {
            if (queryString.length > 0) {
                queryString += '&customer_id=' + customer_id;
            } else {
                queryString += 'customer_id=' + customer_id;
            }
        }

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "GET",
            url: `/wishlists?${queryString}`,
            contentType: "application/json",
            data: ''
        })

        ajax.done(function(res){
            //alert(res.toSource())
            $("#search_results").empty();
            let table = '<table class="table table-striped" cellpadding="10">'
            table += '<thead><tr>'
            table += '<th class="col-md-2">ID</th>'
            table += '<th class="col-md-2">Name</th>'
            table += '<th class="col-md-2">Category</th>'
            table += '<th class="col-md-2">Customer ID</th>'
            table += '<th class="col-md-2">Created Date</th>'
            table += '<th class="col-md-2">Updated Date</th>'
            table += '</tr></thead><tbody>'
            let firstWishlist = "";
            for(let i = 0; i < res.length; i++) {
                let wishlist = res[i];
                table +=  `<tr id="row_${i}"><td>${wishlist.id}</td><td>${wishlist.name}</td><td>${wishlist.category}</td><td>${wishlist.customer_id}</td><td>${wishlist.created_date}</td><td>${wishlist.updated_date}</td></tr>`;
                if (i == 0) {
                    firstWishlist = wishlist;
                }
            }
            table += '</tbody></table>';
            $("#search_results").append(table);

            // copy the first result to the form
            if (firstWishlist != "") {
                update_form_data(firstWishlist)
            }

            flash_message("Success")
        });

        ajax.fail(function(res){
            flash_message(res.responseJSON.message)
        });


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
