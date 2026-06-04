async function loadMembers() {
    try {
        const response = await fetch("/organizer/members");
        const data = await response.json();

        if (!data.success) {
            console.error(data.message);
            return;
        }

        allMembers = data.members;

        renderMembers(allMembers);

    } catch (error) {
        console.error("加载成员列表失败：", error);
    }
}