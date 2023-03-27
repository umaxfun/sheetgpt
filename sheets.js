function getCgptData(prompt) {
  // change me
  // !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  var baseurl = 'https://qqqwwweee.lambda-url.eu-central-1.on.aws'
  // !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

  var url = baseurl + '/api/get_completion';

  var data = {"prompt": prompt}
  var options = {
    'method': 'POST',
    'contentType': 'application/json',
    'payload': JSON.stringify(data)
  };
  var response = UrlFetchApp.fetch(url, options);

  var responseData  = response.getContentText()
  return responseData
}

// simple =sheetGPT("what's the temperature on mars?")
function sheetGPT(question){
  if (!question) {
    question = "How can ChatGPT help in developing complex documents?"
  }
  const postfix = '\nAnswer only using JSON format: {"answer": "<answer>"},'
  var answer = getCgptData(question+postfix)
  var result
  try{
    data = JSON.parse(answer)
    result = data['answer']
    return result
  } catch (err) {
    return err + '\n' + 'data'
  }
}


function junior(question,arraykey,guesskey, param) {
// setting defaults for =junior() to work
if (!question) {
  question = `
Act as a c-level executive assistant. You are tasked to write PR/FAQ about a new product launch. Ask required questions and write a 1-page pr/faq when ready.
answer only in json of the following format:
{
"questions": [ "question1", "question2",...],
"prfaq": "prfaq",
"comments": "if you want to add something freeform"
}
  `
}
  if (!arraykey) arraykey = "questions";
  if (!guesskey) guesskey = "prfaq"

  data = getCgptData(question)
  
  var result
  try{
    data = JSON.parse(data)
    result = [].concat(data[guesskey]).concat(data[arraykey])

  } catch(err){
    return ["err", typeof(data), data, err.toString()]
  }

  if (param === "join"){
    result = result.join('\n')
  }
  console.log(result)
  return result
}