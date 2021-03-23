function changeClass(selectObject, page_name) {
    const class_name = selectObject.value;
    if (class_name === "All") {
        window.location.replace("/admin/" + page_name);
    } else {
        window.location.replace("/admin/" + page_name + "?" + "class_name=" + class_name);
    }
}