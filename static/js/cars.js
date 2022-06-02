let carApp = {};

// Thanks to https://stackoverflow.com/questions/10420352/converting-file-size-in-bytes-to-human-readable-string
/**
 * Format bytes as human-readable text.
 *
 * @param bytes Number of bytes.
 * @param si True to use metric (SI) units, aka powers of 1000. False to use
 *           binary (IEC), aka powers of 1024.
 * @param dp Number of decimal places to display.
 *
 * @return Formatted string.
 */
 function humanFileSize(bytes, si=false, dp=1) {
  const thresh = si ? 1000 : 1024;

  if (Math.abs(bytes) < thresh) {
    return bytes + ' B';
  }

  const units = si
    ? ['kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
    : ['KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB'];
  let u = -1;
  const r = 10**dp;

  do {
    bytes /= thresh;
    ++u;
  } while (Math.round(Math.abs(bytes) * r) / r >= thresh && u < units.length - 1);


  return bytes.toFixed(dp) + ' ' + units[u];
}

let setup = (carApp) => {

  carApp.data = {
    add_car_brand: "",
    add_car_model: "",
    add_car_year: "",
    add_car_price: null,
    add_car_mileage: "",
    add_car_description: "",
    add_car_picture: null,
    add_car_city: "",
    add_car_zip: "",
    // pic_id: null,
    cars: [],
    display: 2,
    file_name: null, // File name
    file_type: null, // File type
    file_date: null, // Date when file uploaded
    file_path: null, // Path of file in GCS
    file_size: null, // Size of uploaded file
    download_url: null, // URL to download a file
    uploading: false, // upload in progress
    deleting: false, // delete in progress
    delete_confirmation: false, // Show the delete confirmation thing.
  };

  carApp.enumerate = (a) => {
    // This adds an _idx field to each element of the array.
    let k = 0;
    a.map((e) => {e._idx = k++;});
    return a;
  };  

  carApp.toggle = function(){
    carApp.vue.display -= 1;
    // carApp.vue.new_post = "";
    carApp.reset_form();
  };

  carApp.file_info = function () {
    if (carApp.vue.file_path) {
        let info = "";
        if (carApp.vue.file_size) {
            info = humanFileSize(carApp.vue.file_size.toString(), si=true);
        }
        if (carApp.vue.file_type) {
            if (info) {
                info += " " + carApp.vue.file_type;
            } else {
                info = carApp.vue.file_type;
            }
        }
        if (info) {
            info = " (" + info + ")";
        }
        if (carApp.vue.file_date) {
            let d = new Sugar.Date(carApp.vue.file_date + "+00:00");
            info += ", uploaded " + d.relative();
        }
        return carApp.vue.file_name + info;
    } else {
        return "";
    }
  };

  carApp.set_result = function (r) {
    // Sets the results after a server call.
    carApp.vue.file_name = r.data.file_name;
    carApp.vue.file_type = r.data.file_type;
    carApp.vue.file_date = r.data.file_date;
    carApp.vue.file_path = r.data.file_path;
    carApp.vue.file_size = r.data.file_size;
    carApp.vue.download_url = r.data.download_url;
  };
  
  carApp.upload_file = function (event, car_idx) {
    console.log("here in upload");
    let input = event.target;
    let file = input.files[0];
    let car = carApp.vue.cars[car_idx];
    if (file) {
        carApp.vue.uploading = true;
        let file_type = file.type;
        let file_name = file.name;
        let file_size = file.size;
        // Requests the upload URL.
        axios.post(obtain_gcs_url, {
            action: "PUT",
            mimetype: file_type,
            file_name: file_name,
            car_id: car.id,
        }).then ((r) => {
            let upload_url = r.data.signed_url;
            let file_path = r.data.file_path;
            // Uploads the file, using the low-level interface.
            let req = new XMLHttpRequest();
            // We listen to the load event = the file is uploaded, and we call upload_complete.
            // That function will notify the server `of the location of the image.
            req.addEventListener("load", function () {
                carApp.upload_complete(file_name, file_type, file_size, file_path, car_idx);
            });
            // TODO: if you like, add a listener for "error" to detect failure.
            req.open("PUT", upload_url, true);
            req.send(file);
        });
    }
    carApp.toggle();
  };
  
  // carApp.upload_file = function (event, car_idx) {
  //   let input = event.target;
  //   let file = input.files[0];
  //   let car = carApp.vue.cars[car_idx];
  //   if (file) {
  //       let reader = new FileReader();
  //       reader.addEventListener("load", function () {
  //           // Sends the image to the server.
  //           axios.post(upload_pic_url,
  //               {
  //                   cars_id: car.id,
  //                   car_picture: reader.result,
  //               })
  //               .then(function () {
  //                   // Sets the local preview.
  //                   car.car_picture = reader.result;

  //               });
  //       });
  //       reader.readAsDataURL(file);
  //   }
  //   carApp.toggle();
  // };

  carApp.delete_file = function () {
    if (!carApp.vue.delete_confirmation) {
        // Ask for confirmation before deleting it.
        carApp.vue.delete_confirmation = true;
    } else {
        // It's confirmed.
        carApp.vue.delete_confirmation = false;
        carApp.vue.deleting = true;
        // Obtains the delete URL.
        let file_path = carApp.vue.file_path;
        axios.post(obtain_gcs_url, {
            action: "DELETE",
            file_path: file_path,
        }).then(function (r) {
            let delete_url = r.data.signed_url;
            if (delete_url) {
                // Performs the deletion request.
                let req = new XMLHttpRequest();
                req.addEventListener("load", function () {
                    carApp.deletion_complete(file_path);
                });
                // TODO: if you like, add a listener for "error" to detect failure.
                req.open("DELETE", delete_url);
                req.send();
            }
        });
    }
  };

  carApp.deletion_complete = function (file_path) {
    // We need to notify the server that the file has been deleted on GCS.
    axios.post(delete_url, {
        file_path: file_path,
    }).then (function (r) {
        // Poof, no more file.
        carApp.vue.deleting =  false;
        carApp.vue.file_name = null;
        carApp.vue.file_type = null;
        carApp.vue.file_date = null;
        carApp.vue.file_path = null;
        carApp.vue.download_url = null;
    })
  };

  carApp.download_file = function (car_idx) {
    let car = carApp.vue.cars[car_idx];
    if (car.download_url) {
        let req = new XMLHttpRequest();
        req.addEventListener("load", function () {
            carApp.do_download(req, car_idx);
        });
        req.responseType = 'blob';
        req.open("GET", car.download_url, true);
        req.send();
    }
  };

  carApp.do_download = function (req, car_idx) {
    let car = carApp.vue.cars[car_idx];
    // This Machiavellic implementation is thanks to Massimo DiPierro.
    // This creates a data URL out of the file we downloaded.
    let data_url = URL.createObjectURL(req.response);
    // Let us now build an a tag, not attached to anything,
    // that looks like this:
    // <a href="my data url" download="myfile.jpg"></a>
    let a = document.createElement('a');
    a.href = data_url;
    a.download = car.file_name;
    // and let's click on it, to do the download!
    a.click();
    // we clean up our act.
    a.remove();
    URL.revokeObjectURL(data_url);
  };

  carApp.upload_complete = function (file_name, file_type, file_size, file_path, car_idx) {
    // We need to let the server know that the upload was complete;
    let car = carApp.vue.cars[car_idx];
    axios.post(notify_url, {
        file_name: file_name,
        file_type: file_type,
        file_path: file_path,
        file_size: file_size,
        car_id: car.id,
    }).then( function (r) {
        car.car_uploading = false;
        car.car_file_name = file_name;
        car.car_file_type = file_type;
        car.car_file_path = file_path;
        car.car_file_size = file_size;
        car.car_file_date = r.data.file_date;
        car.car_download_url = r.data.download_url;
    });
  };

  carApp.add_car = function() {
    axios.post(add_car_url, 
        {
          car_brand: carApp.vue.add_car_brand,
          car_model: carApp.vue.add_car_model,
          car_year: carApp.vue.add_car_year,
          car_price: carApp.vue.add_car_price,
          car_mileage: carApp.vue.add_car_mileage,
          car_description: carApp.vue.add_car_description,
          car_city: carApp.vue.add_car_city,
          car_zip: carApp.vue.add_car_zip,
        }).then(function (response){
          let n = carApp.vue.cars.length;
          carApp.vue.cars.push({
                id: response.data.id,
                car_brand: carApp.vue.add_car_brand,
                car_model: carApp.vue.add_car_model,
                car_year: carApp.vue.add_car_year,
                car_price: carApp.vue.add_car_price,
                car_mileage: carApp.vue.add_car_mileage,
                car_description: carApp.vue.add_car_description,
                car_picture: carApp.vue.pic_id,
                car_city: carApp.vue.add_car_city,
                car_zip: carApp.vue.add_car_zip,
                _idx: n,

                car_file_name: carApp.vue.file_name, // File name
                car_file_type: carApp.vue.file_type, // File type
                car_file_date: carApp.vue.file_date, // Date when file uploaded
                car_file_path: carApp.vue.file_path, // Path of file in GCS
                car_file_size: carApp.vue.file_size, // Size of uploaded file
                car_download_url: carApp.vue.download_url, // URL to download a file
                car_uploading: carApp.vue.uploading, // upload in progress
                car_deleting: carApp.vue.deleting, // delete in progress
                car_delete_confirmation: carApp.vue.delete_confirmation,
            });
            carApp.enumerate(carApp.vue.cars);
            carApp.toggle();
            carApp.reset_form();
        });
  };

  carApp.edit_car = function(id) {
    // console.log("id is", id);
    // console.log(carApp.vue.cars);
    let car;
    for(let i =0; i < carApp.vue.cars.length; i++) {
      if(carApp.vue.cars[i].id === id){
        car = carApp.vue.cars[i];
        break;
      }
    }
    // let car = carApp.vue.cars[id];
    console.log("car", car);
    axios.post(edit_car_url, {
      id: car.id,  
      car_brand: carApp.vue.add_car_brand,
      car_model: carApp.vue.add_car_model,
      car_year: carApp.vue.add_car_year,
      car_price: carApp.vue.add_car_price,
      car_mileage: carApp.vue.add_car_mileage,
      car_description: carApp.vue.add_car_description,
      car_city: carApp.vue.add_car_city,
      car_zip: carApp.vue.add_car_zip,
    }).then(function (response) {
      // console.log("in response");
      console.log(response);
    }).catch(function(error){
      console.log(error);
    });
  };  

  carApp.reset_form = function () {
    carApp.vue.add_car_brand = "";
    carApp.vue.add_car_model = "";
    carApp.vue.add_car_year = "";
    carApp.vue.add_car_price = null;
    carApp.vue.add_car_mileage = "";
    carApp.vue.add_car_description = null;
    carApp.vue.add_car_city = "";
    carApp.vue.add_car_zip = "";
  };

  carApp.computed = {
    file_info: carApp.file_info,
  };

  carApp.methods = {
    add_car: carApp.add_car,
    upload_file: carApp.upload_file, // Uploads a selected file
    toggle: carApp.toggle,
    edit_car: carApp.edit_car,
    upload_file: carApp.upload_file, // Uploads a selected file
    delete_file: carApp.delete_file, // Delete the file.
    download_file: carApp.download_file, // Downloads it.
  };

    // This creates the Vue instance.
    carApp.vue = new Vue({
    el: "#vue-target-cars",
    data: carApp.data,
    computed: carApp.computed,
    methods: carApp.methods
  });

  carApp.setup = () => {
    axios.get(load_cars_info).then(function (response) {
      console.log(response.data.cars);
      carApp.vue.cars = carApp.enumerate(response.data.cars);  
    });

    axios.get(file_info_url).then(function (r) {
      carApp.set_result(r);
    });

  };

  carApp.setup();
};

setup(carApp);