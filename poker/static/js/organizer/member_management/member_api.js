async function loadMembers() {
    try {
        const response = await fetch("/organizer/members");
        const data = await response.json();

        if (!data.success) {
            console.error(data.message);
            return;
        }

        allMembers = data.members;
        organizerCount = data.organizer_count ?? allMembers.filter(m => m.role === "organizer").length;
        maxOrganizers = data.max_organizers ?? 2;

        renderMembers(allMembers);

    } catch (error) {
        console.error("加载成员列表失败：", error);
    }
}