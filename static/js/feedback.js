// This will be the object that will contain the Vue attributes
// and be used to initialize it.
let app = {};

// Given an empty app object, initializes it filling its attributes,
// creates a Vue instance, and then initializes the Vue instance.
let init = (app) => {

    // This is the Vue data.
    app.data = {
        // Complete as you see fit.
        add_mode: false,
        new_post: "",
        like_sentence: "",
        rows: [],
    };

    app.enumerate = (a) => {
        // This adds an _idx field to each element of the array.
        let k = 0;
        a.map((e) => {e._idx = k++;});
        return a;
    };

    app.add_post = function () {
        axios.post(add_post_url,
            {
                post: app.vue.new_post,
            }).then(function (response) {
            app.vue.rows.push({
                // each row contains id, name, post
                id: response.data.id,
                first_name: response.data.first_name,
                last_name: response.data.last_name,
                user_email: response.data.user_email,
                post: app.vue.new_post,
                like: false,
                dislike: false,
                show_likers: false,
            });
            app.enumerate(app.vue.rows);
            app.reset_form();
            app.set_add_status(false);
        });
    };

    app.delete_post = function(row_idx) {
        let id = app.vue.rows[row_idx].id;
        axios.get(delete_post_url, {params: {id: id}}).then(function (response) {
            for (let i = 0; i < app.vue.rows.length; i++) {
                if (app.vue.rows[i].id === id) {
                    app.vue.rows.splice(i, 1);
                    app.enumerate(app.vue.rows);
                    break;
                }
            }
            });
    };

    app.set_add_status = function (new_status) {
        app.vue.add_mode = new_status;
        app.reset_form();
    };

    app.reset_form = function () {
        app.vue.new_post = "";
    };

    app.complete = (rows) => {
        // Initializes useful fields of images.
        rows.map((post) => {
            post.like = false;
            post.dislike= false;
            post.show_likers = false;
        })
        return rows;
    };

    app.set_like = (post_idx) => {
        let post = app.vue.rows[post_idx];
        if (post.like === true) {
            post.like = false;
        }
        else {
            post.like = true;
            post.dislike = false;
        }
        // Sets the like on the server.
        axios.post(set_like_url, {post_id: post.id, like: post.like, dislike: post.dislike});
    };

    app.set_dislike = (post_idx) => {
        let post = app.vue.rows[post_idx];
        if (post.dislike === true) {
            post.dislike = false;
        }
        else {
            post.dislike = true;
            post.like = false;
        }
        // Sets the like on the server.
        axios.post(set_like_url, {post_id: post.id, like: post.like, dislike: post.dislike});
    };

    app.show_likes = (post_idx) => {
        let post = app.vue.rows[post_idx];
        post.show_likers = true;

        // get likers and dislikers
        axios.get(get_likers_url, {params: {"post_id": post.id}})
                    .then(function (result) {
                        app.vue.like_sentence = result.data.final_sentence;
                    })
    };

    app.hide_likes = (post_idx) => {
        let post = app.vue.rows[post_idx];
        post.show_likers = false;

        // app.vue.like_sentence = "";
        post.like_sentence = "";
    };

    // This contains all the methods.
    app.methods = {
        // Complete as you see fit.
        add_post: app.add_post,
        delete_post: app.delete_post,
        set_add_status: app.set_add_status,
        set_like: app.set_like,
        set_dislike: app.set_dislike,
        show_likes: app.show_likes,
        hide_likes: app.hide_likes,
    };

    // This creates the Vue instance.
    app.vue = new Vue({
        el: "#vue-target",
        data: app.data,
        methods: app.methods
    });

    // And this initializes it.
    app.init = () => {
        // get each post
        axios.get(load_posts_url).then(function (response) {
            app.vue.rows = app.complete(app.enumerate(response.data.rows));
        }).then(() => {
            // get likes for each post
            for (let post of app.vue.rows) {
                axios.get(get_likes_url, {params: {"post_id": post.id}})
                    .then(function (result) {
                        post.like = result.data.like;
                        post.dislike= result.data.dislike;
                        console.log(post.like);
                    })
            }
        });
    };

    // Call to the initializer.
    app.init();
};

// This takes the (empty) app object, and initializes it,
// putting all the code i
init(app);
