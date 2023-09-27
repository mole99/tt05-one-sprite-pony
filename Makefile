default: openlane

RTL = src/top.sv \
      src/timing.sv \
      src/sprite_access.sv \
      src/sprite_data.sv \
      src/sprite_movement.sv \
      src/background.sv \
      src/synchronizer.sv \
      src/spi_receiver.sv

sim-icarus:
	iverilog -g2012 -o top.vvp $(RTL) tb/tb_icarus.sv
	vvp top.vvp -fst

sim-verilator:
	verilator --cc --exe --build -j 0 -Wall $(RTL) tb/tb_verilator.cpp -LDFLAGS "-lSDL2 -lpng16"
	./obj_dir/Vtop

sim-cocotb:
	python3 tb/tb_cocotb.py

openlane: $(RTL)
	python3 -m openlane --dockerized --flow Classic --pdk sky130A config.json

sprites:
	python3 sprite2bit.py

animation.gif: images/
	convert -delay 1.666 -loop 0 images/*.png animation.gif

clean:
	rm -f *.vvp *.vcd
	rm -rf openlane_run runs

.PHONY: clean openlane sim-icarus sim-verilator sprites
