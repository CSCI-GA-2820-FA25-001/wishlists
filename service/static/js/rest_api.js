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
                // select the wishlist so items panel is enabled
                setSelectedWishlist(firstWishlist.id);
                // auto-load items for the selected wishlist
                $("#search-items-btn").click();
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

        items.forEach(function (item) {
            var pid  = item.product_id || item.productId || item.id || "";
            var pos  = (item.position !== undefined && item.position !== null) ? item.position : (item.rank || "");
            var desc = item.description || item.desc || "";

            // Render a draggable row and store product id & position in data attributes
            $tbody.append(`
            <tr draggable="true" data-product-id="${pid}" data-position="${pos}">
                <td>${pid}</td>
                <td>${pos}</td>
                <td>${desc}</td>
            </tr>
            `);
        });

        // Attach drag & drop handlers to newly rendered rows
        attachDragHandlers();
    }

    function read_item_inputs() {
        var v;
        v = $("#item_product_id").val();
        var product_id = v ? v.trim() : "";
        v = $("#item_description").val();
        var description = v ? v.trim() : "";
        v = $("#item_before_position").val();
        var before_position = v ? v.trim() : "";
        return { product_id: product_id, description: description, before_position: before_position };
    }

    function setSelectedWishlist(id) {
    selectedWishlistId = (typeof id !== 'undefined' && id !== null) ? id : null;
        const $panel = $("#items_panel");
        const $controls = $("#search-items-btn, #create-item-btn, #update-item-btn, #delete-item-btn, #move-item-btn, #item_product_id");
        const $tbody = $("#items_results_body");
        const $displayId = $("#item_wishlist_id");

        if (!$panel.length) return;

        if (selectedWishlistId) {
            $panel.show();
            $controls.prop("disabled", false);
            if ($displayId.length) $displayId.val(String(selectedWishlistId));
            // Enable the search-items button for the selected wishlist
            $("#search-items-btn").prop("disabled", false);
        } else {
            $panel.hide(); 
            $controls.prop("disabled", true);
            $tbody.empty();
            if ($displayId.length) $displayId.val("");
            $("#search-items-btn").prop("disabled", true);
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
        let name = $("#wishlist_name").val();
        let customer_id = $("#wishlist_customer_id").val();
        let category = $("#wishlist_category").val();
        let description = $("#wishlist_description").val();

        let data = {
            "name": name,
            "customer_id": parseInt(customer_id),
            "category": category,
            "description": description,
        };

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "POST",
            url: "/wishlists",
            contentType: "application/json",
            data: JSON.stringify(data),
        });

        ajax.done(function(res){
            clear_form_data()
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
            // auto-load items when a wishlist is retrieved
            $("#search-items-btn").click();
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
                // enable items panel for this wishlist
                setSelectedWishlist(firstWishlist.id)
                // auto-load items for the selected wishlist
                $("#search-items-btn").click();
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
        if (!requireSelectedWishlist()) return;

        const inputs = read_item_inputs();
        const product_id = inputs.product_id;
        const description = inputs.description;

        if (!product_id) {
            flash_message('Please enter a product id to add');
            return;
        }

        // make product_id an integer, fail if not valid
        const product_id_int = parseInt(product_id);
        if (isNaN(product_id_int)) {
            flash_message('Please enter a valid product id (integer)');
            return;
        }

        
        let data = {
            "product_id": product_id_int,
            "description": description
        };
        let ajax = $.ajax({
            type: "POST",
            url: `/wishlists/${selectedWishlistId}/items`,
            contentType: "application/json",
            data: JSON.stringify(data),
        });

        ajax.done(function(res){
            // Refresh items
            $("#search-items-btn").click();
            flash_message("Item added successfully");
        }
        );

        ajax.fail(function(res){
            var msg = (res && res.responseJSON && res.responseJSON.message) ? res.responseJSON.message : 'Server error when adding item';
            flash_message(msg);
        });


    });

    // ****************************************
    // Update a Wishlist Item
    // ****************************************
    $("#update-btn").click(function () {
        let wishlist_id = $("#wishlist_id").val();
        let name = $("#wishlist_name").val();
        let description = $("#wishlist_description").val();
        let category = $("#wishlist_category").val();

        $("#flash_message").empty();

        let data = {
            "name": name,
            "description": description,
            "category": category
        };

        let ajax = $.ajax({
            type: "PUT",
            url: `/wishlists/${wishlist_id}`,
            contentType: "application/json",
            data: JSON.stringify(data),
        });

        ajax.done(function(res){
            update_form_data(res);
            flash_message("Wishlist has been Updated!");
        });

        ajax.fail(function(res){
            flash_message("Server error when updating!");
        });
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

        if (!requireSelectedWishlist()) return;

        let wishlist_id = selectedWishlistId;

        let ajax = $.ajax({
            type: "GET",
            url: `/wishlists/${wishlist_id}/items`,
            contentType: "application/json",
            data: ''
        })

        ajax.done(function(res){
            render_items(res);
            flash_message("Success");
        });

        ajax.fail(function(res){
            var msg = (res && res.responseJSON && res.responseJSON.message) ? res.responseJSON.message : 'Error retrieving items';
            flash_message(msg);
        });

    });


    // ****************************************
    // Move for a Wishlist Item
    // ****************************************

    $("#move-item-btn").click(function () {

        // Fallback: move via explicit product id + before_position input
        if (!requireSelectedWishlist()) return;

        const inputs = read_item_inputs();
        const product_id = inputs.product_id;
        const before_position = inputs.before_position;

        if (!product_id) {
            flash_message('Please enter a product id to move');
            return;
        }
        if (!before_position || isNaN(parseInt(before_position))) {
            flash_message('Please enter a valid before_position (integer)');
            return;
        }

        let ajax = $.ajax({
            type: 'PATCH',
            url: `/wishlists/${selectedWishlistId}/items/${product_id}`,
            contentType: 'application/json',
            data: JSON.stringify({ before_position: parseInt(before_position) })
        });

        ajax.done(function(res){
            // Refresh items
            $("#search-items-btn").click();
            flash_message('Item reordered successfully');
        });

        ajax.fail(function(res){
            var msg = (res && res.responseJSON && res.responseJSON.message) ? res.responseJSON.message : 'Server error when moving item';
            flash_message(msg);
        });

    });


    // -----------------
    // Drag & drop helpers
    // -----------------
    function attachDragHandlers() {
        const $tbody = $("#items_results_body");

        $tbody.find('tr').each(function () {
            const $row = $(this);

            // Ensure events aren't doubled
            $row.off('dragstart dragend dragover dragenter dragleave drop');

            $row.on('dragstart', function (ev) {
                ev.originalEvent.dataTransfer.setData('text/plain', $row.data('product-id'));
                $row.addClass('dragging');
            });

            $row.on('dragend', function () {
                $row.removeClass('dragging');
                $tbody.find('.dragover').removeClass('dragover');
            });

            $row.on('dragover', function (ev) {
                ev.preventDefault(); // allow drop
            });

            $row.on('dragenter', function (ev) {
                $(this).addClass('dragover');
            });

            $row.on('dragleave', function (ev) {
                $(this).removeClass('dragover');
            });

            $row.on('drop', function (ev) {
                ev.preventDefault();
                $(this).removeClass('dragover');

                var draggedProductId = ev.originalEvent.dataTransfer.getData('text/plain');
                var targetProductId = $(this).data('product-id');
                var targetPosition = $(this).data('position');

                if (!draggedProductId || (targetPosition === undefined || targetPosition === null)) {
                    flash_message('Invalid drag/drop target');
                    return;
                }

                // Find the dragged row in the table to determine its original position
                var $draggedRow = $tbody.find('tr[data-product-id="' + draggedProductId + '"]');
                var draggedPos = null;
                if ($draggedRow.length > 0) {
                    draggedPos = $draggedRow.data('position');
                }

                // Compute before_position depending on move direction
                var $next = $(this).next('tr');
                var beforePos = null;
                if (draggedPos !== null && draggedPos !== undefined && parseInt(draggedPos, 10) > parseInt(targetPosition, 10)) {
                    // moving up: insert before target
                    beforePos = parseInt(targetPosition, 10);
                } else {
                    // moving down or unknown: insert before next row (i.e., after target)
                    if ($next.length > 0) {
                        beforePos = $next.data('position');
                    } else {
                        var tp = parseInt(targetPosition, 10) || 0;
                        beforePos = tp + 1000;
                    }
                }

                if (beforePos === undefined || beforePos === null) {
                    flash_message('Could not determine insertion position');
                    return;
                }

                // Send PATCH to move dragged item before the computed position
                var ajax = $.ajax({
                    type: 'PATCH',
                    url: '/wishlists/' + selectedWishlistId + '/items/' + draggedProductId,
                    contentType: 'application/json',
                    data: JSON.stringify({ before_position: parseInt(beforePos, 10) })
                });

                ajax.done(function(res){
                    // Refresh items list after successful move
                    $("#search-items-btn").click();
                    flash_message('Item reordered successfully');
                });

                ajax.fail(function(res){
                    var msg = (res && res.responseJSON && res.responseJSON.message) ? res.responseJSON.message : 'Error reordering item';
                    flash_message(msg);
                });
            });
        });
    }

})
