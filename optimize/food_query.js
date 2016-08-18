/* Query to extract the foods we will use from the MongoDB
 *
 * We assume the default collection (nndb) used by nndb-import
 *
 * This logic is mainly:
 *  - We want only the survey foods (since the nutritional info is complete)
 *  - We want only food in certain food groups (see below)
 *
 * Also note that we were going to exclude "breakfast cereals" but we opted
 * to hand-select Kashi brand cereals only from the group.
 *
 * Food Groups included:
 *      1100 - Vegetables and Vegetable Products
 *      1600 - Legumes and Legume Products
 *      1200 - Nut and Seed Products
 *      0900 - Fruits and Fruit Juices
 *      2000 - Cereal Grains and Pasta
 *      0800 - Breakfast Cereals (NOTE: only Kashi products)

 * For now we are leaving these out
 *      0100 - Dairy and Egg Products
 *      1500 - Finfish and Shellfish Products
 *      0500 - Poultry Products
 *      1000 - Pork Products
 *      1300 - Beef Products
 * */

db.getCollection('nndb').find({
    $and: [
        { survey: 'Y' },
        {$or: [
            { food_group_code:
                { $in: ["1100", "1600", "1200", "0900", "2000"]
                }
            },
            { $and: [
                {food_group_code: '0800'},
                {descrip: RegExp("KASHI", "i") }
            ]}
        ]}
    ]
})
.forEach(function(f) {
    printjsononeline(f);
});
