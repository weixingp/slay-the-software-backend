function changeWorld(selectObject) {
    const world_name = selectObject.value
    window.location.replace("/admin/campaign_statistics?world=" + world_name)
}

function changeClass(selectObject) {
    const world_name = document.getElementById("select-world").value;
    const class_name = selectObject.value;
    if (class_name === "All") {
        window.location.replace("/admin/campaign_statistics?world=" + world_name);
    } else {
        window.location.replace("/admin/campaign_statistics?world=" + world_name + "&class=" + class_name);
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