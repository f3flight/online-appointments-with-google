
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
		var checked = false;
		for (x in dateDict[v]) {
			var hours = parseInt(x.substr(0,2));
			var suffix = hours >= 12 ? " pm" : " am";
			hours = ((hours + 11) % 12 + 1);
			var time_txt = hours + x.substr(2,3) + suffix;
			slots.innerHTML += '<input type="radio" name="slot" value="' +
				dateDict[v][x]['id'] + '"' + (checked ? '' : ' checked="checked"') + ' />' + time_txt + '<br />';
			checked = true;
		};
		if (v in dateDict) {
			slots.innerHTML += '<br /><label for="name">Name: </label><input type="text" placeholder="Alex Doe" name="name" required/><br /><label for="phone">Phone: </label><input type="text" placeholder="+14081234567" name="phone" required/><br /><label for="email">Email: </label><input type="email" placeholder="abc@gmail.com" name="email"/><br /><br /><input type="submit" value="Schedule!" />';
		};
	});
};
