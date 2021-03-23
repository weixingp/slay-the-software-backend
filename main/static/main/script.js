function changeClass(selectObject) {
    const class_name = selectObject.value;
    if (class_name === "All") {
        window.location.replace("/admin/campaign_statistics/");
    } else {
        window.location.replace("/admin/campaign_statistics?" + "class=" + class_name);
    }
}

function changeAssignment(selectObject) {
    const access_code = selectObject.value;
    if (access_code === "All") {
        window.location.replace("/admin/assignment_statistics/");
    } else {
        window.location.replace("/admin/assignment_statistics?access_code=" + access_code);
    }
}

function changeAssignmentClass(selectObject) {
    const access_code = document.getElementById("select-assignment").value;
    const class_name = selectObject.value;
    if (class_name == "All") {
        window.location.replace("/admin/assignment_statistics?access_code=" + access_code);
    } else {
        window.location.replace("/admin/assignment_statistics?access_code=" + access_code + "&class=" + class_name);
    }
}