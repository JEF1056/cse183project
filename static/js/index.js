let app = {};


// Given an empty app object, initializes it filling its attributes,
// creates a Vue instance, and then initializes the Vue instance.
let init = (app) => {

    // This is the Vue data.
    app.data = {
        // Complete as you see fit.
        query: "",
        results: [],
        range: "",
        city: "",
        min_year: "",
        max_year: "",
        selected: "",
        car_model: "",
        min_price: "",
        max_price: "",
        min_mil: "",
        max_mil: "",
    };

    app.enumerate = (a) => {
        // This adds an _idx field to each element of the array.
        let k = 0;
        a.map((e) => {
            e._idx = k++;
        });
        return a;
    };


    app.filter = function () {
        if (app.vue.selected.length > 1 || app.vue.min_year.length > 1 || app.vue.max_year.length > 1 ||
            app.vue.car_model.length > 1 || app.vue.min_price.length > 1 || app.vue.max_price.length > 1 ||
            app.vue.min_mil.length > 1 || app.vue.max_mil.length > 1 || app.vue.range.length>1 && app.vue.city.length>1
        ) {
            axios.get(filter_url, {
                params: {
                    s: app.vue.selected,
                    city: app.vue.city,
                    range: app.vue.range,
                    min_year: app.vue.min_year,
                    max_year: app.vue.max_year,
                    car_model: app.vue.car_model,
                    min_price: app.vue.min_price,
                    max_price: app.vue.max_price,
                    min_mil: app.vue.min_mil,
                    max_mil: app.vue.max_mil
                }
            })
                .then(function (result) {
                    app.vue.results = result.data.results;
                });
        } else {
            app.vue.results = [];
        }
    }


    // This contains all the methods.
    app.methods = {
        // Complete as you see fit.
        filter: app.filter
    };

    // This creates the Vue instance.
    app.vue = new Vue({
        el: "#vue-target",
        data: app.data,
        methods: app.methods
    });

    // And this initializes it.
    app.init = () => {
        // Put here any initialization code.
        // Typically this is a server GET call to load the data.
        axios.get(load_cars).then(function (response){
            app.vue.results = app.enumerate(response.data.results);
        })

        axios.get(get_cars_url).then(function (r1){
            app.vue.results = app.enumerate(r1.data.results);
        })

        alert(1);
    };

    // Call to the initializer.
    app.init();
};

// This takes the (empty) app object, and initializes it,
// putting all the code i
init(app);