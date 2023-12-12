$(document).ready(function() {

	// Set the token so that we are not rejected by server
	var csrf_token = $('meta[name=csrf-token]').attr('content');
	
	// Configure ajaxSetup so that the CSRF token is added to the header of every request
	$.ajaxSetup({
	    beforeSend: function(xhr, settings) {
	        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
	            xhr.setRequestHeader("X-CSRFToken", csrf_token);
	        }
	    }
	});

	$("a.vote").on("click", function() {
		var clicked_obj = $(this);

		// Which product was clicked?
		var product_id = $(this).attr('id');

		$.ajax({
			url: '/like',
			type: 'POST',
			data: JSON.stringify({ product_id: product_id }),
			contentType: "application/json; charset=utf-8",
        	dataType: "json",
			success: function(response){
				console.log(response);
				// Update the html rendered to reflect new count
				clicked_obj.children()[1].innerHTML = " " + response.likes
				updateIcon(clicked_obj, response.liked)
				if(window.location.pathname === '/viewliked'){
					location.reload();
				}
			},
			error: function(error){
				console.log(error);
			}
		});

	});

	$("a.stock").on("click", function() {

		// Which product was clicked?
		var product_id = $(this).attr('id');
		var vote_type = $(this).children()[0].id;

		$.ajax({
			url: '/stock',
			type: 'POST',
			data: JSON.stringify({ product_id: product_id, vote_type: vote_type}),
			  // We are using JSON, not XML
			contentType: "application/json; charset=utf-8",
			dataType: "json",
			success: function(response){
				console.log(response);
				// Update the html rendered to reflect new count
				// Check which count to update
				$(".sstock[data-productid='" + product_id + "']").html(" " + response.quantity_left);
			},
			error: function(error){
				console.log(error);
			}
		});
	});

	function updateIcon(clicked_obj, liked) {
        // Update the icon based on the 'liked' property
        var icon = clicked_obj.find("i");
        icon.removeClass("far fa-heart fas fa-heart");
        icon.addClass(liked ? "fas fa-heart" : "far fa-heart");
    }	  

});
