'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const {locate,paragraphs}=require('../workshop/static/anchors.js');
function issue(body,quote,paragraph=1,occurrence=1) {
  const p=paragraphs(body)[paragraph-1];let at=-1;
  for(let i=0;i<occurrence;i++)at=p.text.indexOf(quote,at+1);
  const start=p.start+at;
  return {paragraph,quote,start:Array.from(body.slice(0,start)).length,end:Array.from(body.slice(0,start+quote.length)).length};
}
test('selects an exact original range without mutation',()=>{const body='The robot is really ready.';assert.deepEqual(locate(issue(body,'really'),body,body),{start:13,end:19,basis:'same-draft'});});
test('converts Unicode code points to UTF-16 offsets',()=>{const body='👩🏽‍💻 A robot is ready.';const range=locate(issue(body,'robot'),body,body);assert.equal(body.slice(range.start,range.end),'robot');assert.equal(range.start,body.indexOf('robot'));});
test('follows one unchanged moved paragraph',()=>{const body='First.\n\nSecond is ready.';const current='A new paragraph.\n\nSecond is ready.\n\nFirst.';const range=locate(issue(body,'ready',2),body,current);assert.equal(range.basis,'unchanged-paragraph');assert.equal(current.slice(range.start,range.end),'ready');});
test('does not guess a changed quotation',()=>{const body='The robot is ready.';assert.equal(locate(issue(body,'ready'),body,'The robot is awake.'),null);});
test('does not guess when the old quote survives but paragraph changed',()=>{const body='The robot is ready.';assert.equal(locate(issue(body,'ready'),body,'The operator is ready.'),null);});
test('rejects ambiguous duplicate paragraphs after edits',()=>{const body='The robot is ready.';assert.equal(locate(issue(body,'ready'),body,body+'\n\n'+body),null);});
test('honors a second quote occurrence in an unchanged paragraph',()=>{const body='ready, ready.';const i=issue(body,'ready',1,2);const current='New.\n\n'+body;const range=locate(i,body,current);assert.equal(range.start,current.lastIndexOf('ready'));assert.equal(current.slice(range.start,range.end),'ready');});
test('supports blank lines containing tabs and spaces',()=>{const body='One.\n \n\t\nTwo has a robot.';const current='New.\n\n'+body;const range=locate(issue(body,'robot',2),body,current);assert.equal(current.slice(range.start,range.end),'robot');});
test('rejects corrupt stored offsets',()=>{const body='A robot.';const i=issue(body,'robot');i.start=0;assert.equal(locate(i,body,body),null);});
test('identical repeated paragraph is safe when the entire draft is unchanged',()=>{const body='Robot.\n\nRobot.';const range=locate(issue(body,'Robot',2),body,body);assert.equal(range.start,8);});
