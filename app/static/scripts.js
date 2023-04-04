// This is similar to an import statement in python
// Here the library containing the moment() function is imported
document.writeln("<script src='https://momentjs.com/downloads/moment.js'></script>");
function toMoment(input_timestamps) {
    const output_timestamps = [];
    for (let item of input_timestamps) {
    output_timestamps.push(moment(item).format("DD MM YYYY HH:mm:ss"));
    }
    return output_timestamps;
}
function toMomentSingle(input_timestamp) {
    var output_timestamps = null;
    output_timestamps = moment(input_timestamp).format("YYYY-MM-DDTHH:mm");
    return output_timestamps;
}