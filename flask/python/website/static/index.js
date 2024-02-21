

function deductBalance() {
  fetch("/deduct", {
    method: "POST",
    body: JSON.stringify({}),
    headers: {
      "Content-Type": "application/json",
    },
  }).then((res) => {
    if (res.ok) {
      // Handle success response
      console.log("Deduction successful");
      window.location.reload(); // Reload the page to reflect the updated balance
    } else {
      // Handle error response
      console.error("Failed to deduct balance");
    }
  }).catch((error) => {
    console.error("Error:", error);
  });
}

