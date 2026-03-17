console.log("websocket.js loaded");

(function () {

    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const wsUrl = `${protocol}://${window.location.host}/websocket/`;

    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
        console.log("WebSocket connected");
    };

    socket.onerror = (e) => {
        console.log("WebSocket error:", e);
    };

    socket.onclose = () => {
      console.log("WebSocket closed, reconnecting...");
      setTimeout(() => location.reload(), 3000);
  };

    socket.onmessage = function (e) {

        const payload = JSON.parse(e.data);

        console.log("Realtime payload:", payload);

        const type = payload.type;

        /*
        Example payload from backend:

        {
            type: "notification",
            message: "New notification",
            count: 3
        }
        */

        switch (type) {

            case "notification":

                const badge = document.getElementById("notif-badge");

                if (badge && payload.count !== undefined && payload.count !== null) {
                    

                    if (payload.count > 0) {
                        badge.textContent = payload.count;
                        badge.style.display = "inline-block";
                    } else {
                        badge.style.display = "none";
                    }
                }

                if (payload.message) {
                    console.log(payload.message);
                }

                break;


            case "dashboard_update":

                console.log("Dashboard update:", payload.data);

                // Example:
                // update dashboard cards if elements exist

                const pending = document.getElementById("pending-count");

                if (pending && payload.data && payload.data.pending_tasks !== undefined) {
                    pending.textContent = payload.data.pending_tasks;
                }

                break;


            case "dashboard_utilization":
                const data = payload.data || {};
                const activityId = data.activity_id;
                const currentParticipants = Number(data.current_participants || 0);
                const maxCapacity = Number(data.max_capacity || 0);

                let utilizationPercent = 0;
                if (maxCapacity > 0) {
                   utilizationPercent = Math.round((currentParticipants / maxCapacity) * 100);
                }

                const countEl = document.getElementById(`slot-count-${activityId}`);
                const barEl = document.getElementById(`slot-bar-${activityId}`);
                const percentEl = document.getElementById(`slot-percent-${activityId}`);

                if (countEl) {
                    countEl.textContent = `${currentParticipants} / ${maxCapacity}`;
                }

                if (barEl) {
                    barEl.style.width = `${utilizationPercent}%`;
                }

                if (percentEl) {
                    percentEl.textContent = `${utilizationPercent}% filled`;
                }

                console.log("Dashboard Utilization:", data);
                break;
                
                
            default:
                console.log("Unknown websocket event:", payload);

        }

    };

})();