async function loadUsers() {
    try {
        const response = await fetch("/admin/users");
        const data = await response.json();

        if (!data.success) {
            console.error(data.message);
            return;
        }

        allUsers = data.users;

        renderUsers(allUsers);

    } catch (error) {
        console.error("加载用户列表失败：", error);
    }
}