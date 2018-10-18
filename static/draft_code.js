
dateDict = {}

build_date_str = d => {
	dateStr = d.getFullYear() +
		'-' + ('0' + (d.getMonth() + 1)).slice(-2) +
		'-' + ('0' + d.getDate()).slice(-2);
	return dateStr;
};

init = () => {

	for (datetime in dates) {
		dateStr = datetime.substr(0,10);
		timeStr = datetime.substr(11,5);
		if (!(dateStr in dateDict)) {
			dateDict[dateStr] = {}
		}
		dateDict[dateStr][timeStr] = dates[datetime]
	}


	const opts = {
		'dateValidator': d => {
			dateStr = build_date_str(d);
			if (dateStr in dateDict) {
				return true;
			} else {
				return false;
			}
		},
		'time': false
	};
	cal = document.getElementById('calendar');
	slots = document.getElementById('slots');
	message = document.getElementById('message');
	rome(cal, opts).on('data', v => {
		slots.innerHTML = "";
		if (v in dateDict) {
			message.innerText = 'Please select an available slot on ' +
				v + ':'
		};
		for (x in dateDict[v]) {
			slots.innerHTML += '<input type="radio" name="slot" value="' +
				dateDict[v][x]['id'] + '" />' + x + '<br />';
		};
		if (v in dateDict) {
			slots.innerHTML += '<label for="name">Name:</label><input type="text" placeholder="John Doe" name="name" required/><br /><label for="phone">Phone:</label><input type="text" placeholder="+14081234567" name="phone" required/><br /><label for="email">Email:</label><input type="email" placeholder="abc@gmail.com" name="email"/><br /><input type="submit" value="book" />';
		};
	});
};
