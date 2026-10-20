async function fetchGroupInfo() {
    const response = await fetch("/organizer/group-info");
    return await response.json();
}

async function apiUpdateGroupName(groupName) {
    const formData = new FormData();
    formData.append("group_name", groupName);
    const response = await fetch("/organizer/update-group-name", {
        method: "POST",
        body: formData,
    });
    return await response.json();
}
