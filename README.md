# VagrantStory-Font

Vagrant Story font replacement:

1. Place your "Vagrant Story (USA).bin" in the bin folder
2. Edit the font_edit.png however you like.
	NOTE:
	The font palette is greyscale, from white to black, with 1 fully transparent entry.
	You have to take this into account when editing the font image.
		i.e. If you are using a black font in an editing program, you have to convert it
		so the fainter pixel are whiter, and the stronger pixels are darker.
		This can be done easily in photoshop by adding a white background to the text,
		and then selecting all the pure white pixels with the magic selection tool and
		deleting them.
	The font image uses 12x12 cells for each letter, so set your grid size to that in photoshop.

4. Run font.py
5. Your bin file is now patched!
