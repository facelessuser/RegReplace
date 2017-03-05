[![Unix Build Status][travis-image]][travis-link]
[![Package Control Downloads][pc-image]][pc-link]
![License][license-image]
# About

Reg Replace is a plugin for Sublime Text that allows the creating of commands consisting of sequences of find and replace instructions.

![edit panel](https://dl.dropboxusercontent.com/u/342698/RegReplace/edit_panel.png)

# Features

- Create find and replace rules that can then be used to create Sublime Commands to call at any time.
- Chain multiple regex find and replace rules together.
- Create rules that can filter regex results by syntax scope.
- Create rules that target specific scopes and apply regex to the content.
- Create commands that highlight results and requiring confirmation before replacing.
- Create find and fold/unfold commands to fold or unfold the find results instead of replacing them.
- Create find and mark/unmark commands to simply highlight or unhighlight results instead of replacing them.
- Create find and select commands to select certain results instead of replacing them.
- Create advanced commands that can run a plugin to do more complex replaces.

# Documentation

http://facelessuser.github.io/RegReplace/

# License

Reg Replace is released under the MIT license.

Copyright (c) 2011 - 2017 Isaac Muse <isaacmuse@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

[travis-image]: https://img.shields.io/travis/facelessuser/RegReplace/master.svg
[travis-link]: https://travis-ci.org/facelessuser/RegReplace
[pc-image]: https://img.shields.io/packagecontrol/dt/RegReplace.svg
[pc-link]: https://packagecontrol.io/packages/RegReplace
[license-image]: https://img.shields.io/badge/license-MIT-blue.svg
