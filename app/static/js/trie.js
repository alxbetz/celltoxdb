class Node {
 constructor() {
 this.children = new Map();
 this.value = "";
 }
 
 find(node,key) {
 
 for (const c of key) {
 if (node.children.has(char)) {
     node = node.children[char]
 } else {
 
 return null;
 }
 
 }
 return node.value
 
 }

 insert(node,key,value) {
 for (const char of key) {
 if (!node.children.has(char)) {
     node.children[char] = new Node()
 } 
 
 node = node.children[char]
 }
 node.value = value
 }

}