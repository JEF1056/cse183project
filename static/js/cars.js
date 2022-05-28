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
  }
  
  carApp.upload_file = function (event, car_idx) {
    let input = event.target;
    let file = input.files[0];
    let car = carApp.vue.cars[car_idx];
    if (file) {
        let reader = new FileReader();
        reader.addEventListener("load", function () {
            // Sends the image to the server.
            axios.post(upload_pic_url,
                {
                    cars_id: car.id,
                    car_picture: reader.result,
                })
                .then(function () {
                    // Sets the local preview.
                    car.car_picture = reader.result;

                });
        });
        reader.readAsDataURL(file);
    }
    carApp.toggle();
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
            });
            carApp.enumerate(carApp.vue.cars);
            carApp.toggle();
            carApp.reset_form();
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

  carApp.methods = {
    add_car: carApp.add_car,
    upload_file: carApp.upload_file, // Uploads a selected file
    toggle: carApp.toggle
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
      // console.log(response.data.cars);
    });

    // axios.get(file_info_url)
    //   .then(function (r) {
    //     carApp.set_result(r);
    //   });
  };

  carApp.setup();
};

setup(carApp);