/** CustomerRecord — stores customer profile data */
class CustomerRecord {
    constructor(id, firstName, lastName, email) {
        this._id = id || null;
        this._firstName = firstName || null;
        this._lastName = lastName || null;
        this._email = email || null;
        this._phone = null;
        this._address = null;
        this._city = null;
        this._state = null;
        this._zipCode = null;
        this._country = null;
        this._active = true;
        this._createdDate = new Date();
        this._lastModified = null;
    }

    // Getters
    getId() { return this._id; }
    getFirstName() { return this._firstName; }
    getLastName() { return this._lastName; }
    getEmail() { return this._email; }
    getPhone() { return this._phone; }
    getAddress() { return this._address; }
    getCity() { return this._city; }
    getState() { return this._state; }
    getZipCode() { return this._zipCode; }
    getCountry() { return this._country; }
    isActive() { return this._active; }
    getCreatedDate() { return this._createdDate; }
    getLastModified() { return this._lastModified; }

    // Setters
    setId(id) { this._id = id; }
    setFirstName(firstName) { this._firstName = firstName; }
    setLastName(lastName) { this._lastName = lastName; }
    setEmail(email) { this._email = email; }
    setPhone(phone) { this._phone = phone; }
    setAddress(address) { this._address = address; }
    setCity(city) { this._city = city; }
    setState(state) { this._state = state; }
    setZipCode(zipCode) { this._zipCode = zipCode; }
    setCountry(country) { this._country = country; }
    setActive(active) { this._active = active; }
    setCreatedDate(date) { this._createdDate = date; }
    setLastModified(date) { this._lastModified = date; }
}


/** ProductDTO — product catalogue entry */
class ProductDTO {
    constructor() {
        this._productId = null;
        this._name = null;
        this._description = null;
        this._price = 0;
        this._stockQuantity = 0;
        this._category = null;
        this._manufacturer = null;
        this._weight = 0;
        this._dimensions = null;
    }

    getProductId() { return this._productId; }
    setProductId(id) { this._productId = id; }
    getName() { return this._name; }
    setName(name) { this._name = name; }
    getDescription() { return this._description; }
    setDescription(desc) { this._description = desc; }
    getPrice() { return this._price; }
    setPrice(price) { this._price = price; }
    getStockQuantity() { return this._stockQuantity; }
    setStockQuantity(qty) { this._stockQuantity = qty; }
    getCategory() { return this._category; }
    setCategory(cat) { this._category = cat; }
    getManufacturer() { return this._manufacturer; }
    setManufacturer(mfr) { this._manufacturer = mfr; }
    getWeight() { return this._weight; }
    setWeight(w) { this._weight = w; }
    getDimensions() { return this._dimensions; }
    setDimensions(dim) { this._dimensions = dim; }
}

module.exports = { CustomerRecord, ProductDTO };
