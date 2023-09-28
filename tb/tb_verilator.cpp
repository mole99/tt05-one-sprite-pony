#include <iostream>
#include <cmath>
#include <vector>
#include <cstdlib>
#include <sstream>
#include <iomanip>
#include <filesystem>

#include <png.h>
#include <SDL2/SDL.h>

#include "Vtop.h"
#include "verilated.h"

#define WINDOW_WIDTH  800
#define WINDOW_HEIGHT 600

#define HFRONT 40
#define HSYNC 128
#define HBACK 88

#define VFRONT 1
#define VSYNC 4
#define VBACK 23

#define SAVE_IMAGES

void save_png(const char* file_name, uint8_t framebuffer[WINDOW_WIDTH * WINDOW_HEIGHT * 4]);

int main(int argc, char **argv) {

    // Check if "images" folder exists
    if (!std::filesystem::is_directory("images") || !std::filesystem::exists("images")) {
        std::filesystem::create_directory("images"); // create "images" folder
    }

    uint8_t framebuffer[WINDOW_WIDTH * WINDOW_HEIGHT * 4];

    Verilated::commandArgs(argc, argv);
    Vtop *top = new Vtop;

    // perform a reset
    top->clk = 0;
    top->eval();
    top->reset_n = 0;
    top->clk = 1;
    top->eval();
    top->reset_n = 1;

    SDL_Init(SDL_INIT_VIDEO);

    SDL_Window* window = SDL_CreateWindow(
        "Framebuffer Verilator",
        SDL_WINDOWPOS_UNDEFINED,
        SDL_WINDOWPOS_UNDEFINED,
        WINDOW_WIDTH,
        WINDOW_HEIGHT,
        0
    );

    SDL_Renderer* renderer = SDL_CreateRenderer(
        window,
        -1,
        SDL_RENDERER_ACCELERATED
    );

    SDL_SetRenderDrawColor(renderer, 0, 0, 0, SDL_ALPHA_OPAQUE);
    SDL_RenderClear(renderer);

    SDL_Event e;

    SDL_Texture* texture =
        SDL_CreateTexture(
        renderer,
        SDL_PIXELFORMAT_ARGB8888,
        SDL_TEXTUREACCESS_STREAMING,
        WINDOW_WIDTH,
        WINDOW_HEIGHT
    );

    bool quit = false;

    int hnum = 0;
    int vnum = 0;

    bool prev_hsync = false;
    bool prev_vsync = false;

    int image_number = 0;

    while (!quit) {

        while (SDL_PollEvent(&e) == 1) {
            if (e.type == SDL_QUIT) {
                quit = true;
            } else if (e.type == SDL_KEYDOWN) {
                switch (e.key.keysym.sym) {
                    case SDLK_q:
                        quit = true;
                    default:
                        break;
                }
            }
        }

        auto keystate = SDL_GetKeyboardState(NULL);

        top->reset_n = !keystate[SDL_SCANCODE_ESCAPE];

        if (keystate[SDL_SCANCODE_S]) {
            save_png("screenshot.png", framebuffer);
        }

        // simulate for 20000 clocks
        for (int i = 0; i < 20000; ++i) {

            static int cnt = 0;

            //std::cout << cnt << std::endl;

            // This is for inc by 4 mode
            if (cnt==0 || 1)
            {
              top->clk = 0;
              top->eval();
              top->clk = 1;
              top->eval();
            }
            
            if (cnt++ == 3)
            {
              cnt = 0;
            }


            if (top->hsync) {
                hnum = -HBACK - 1;
                //std::cout << "hsync" << std::endl;
            }

            if (top->vsync) {
                vnum = -VBACK - 1;
                //std::cout << "vsync" << std::endl;
            }

            // active frame
            if ((hnum >= 0) && (hnum < WINDOW_WIDTH) && (vnum >= 0) && (vnum < WINDOW_HEIGHT)) {
                //std::cout << "pixel at " << hnum << ", " << vnum << " with " << unsigned(top->rrggbb) << std::endl;

                uint8_t r = (top->rrggbb & 0b000011) >> 0 << 6;
                if (r & 0b01000000) r |= 0b00111111;

                uint8_t g = (top->rrggbb & 0b001100) >> 2 << 6;
                if (g & 0b01000000) g |= 0b00111111;

                uint8_t b = (top->rrggbb & 0b110000) >> 4 << 6;
                if (b & 0b01000000) b |= 0b00111111;

                framebuffer[(vnum * WINDOW_WIDTH + hnum) * 4 + 0] = r;
                framebuffer[(vnum * WINDOW_WIDTH + hnum) * 4 + 1] = g;
                framebuffer[(vnum * WINDOW_WIDTH + hnum) * 4 + 2] = b;
            }

            hnum++;

            // h and v blank logic
            if (!prev_hsync && top->hsync) {
            vnum++;
            //std::cout << "next line" << std::endl;
            }

            if (!prev_vsync && top->vsync) {
                SDL_UpdateTexture(
                    texture,
                    NULL,
                    framebuffer,
                    WINDOW_WIDTH * 4
                );

                SDL_RenderCopy(
                    renderer,
                    texture,
                    NULL,
                    NULL
                );

                SDL_RenderPresent(renderer);
                
                if (1) {
                    std::ostringstream ostr;
                    ostr << "images/img_" << std::setfill('0') << std::setw(4) << image_number++ << ".png";
                  
                    #ifdef SAVE_IMAGES
                    save_png(ostr.str().c_str(), framebuffer);
                    #endif
                }
            }

            prev_hsync = top->hsync;
            prev_vsync = top->vsync;
        }
    }

    top->final();
    delete top;

    SDL_DestroyRenderer(renderer);
    SDL_DestroyWindow(window);
    SDL_Quit();

    return EXIT_SUCCESS;
}

void save_png(const char* file_name, uint8_t framebuffer[WINDOW_WIDTH * WINDOW_HEIGHT * 4]) {
    int pixel_size = 3;
    int depth = 8;

    FILE *p_file = fopen(file_name, "wb");
    if (!p_file) {
        abort();
    }
    png_structp p_png = png_create_write_struct (PNG_LIBPNG_VER_STRING, NULL, NULL, NULL);
    if (p_png == NULL) {
        abort();
    }
    png_infop p_info = png_create_info_struct (p_png);
    if (p_info == NULL) {
        abort();
    }
    if (setjmp (png_jmpbuf (p_png))) {
        abort();
    }

    png_set_IHDR (p_png,
        p_info,
        WINDOW_WIDTH,
        WINDOW_HEIGHT,
        depth,
        PNG_COLOR_TYPE_RGB,
        PNG_INTERLACE_NONE,
        PNG_COMPRESSION_TYPE_DEFAULT,
        PNG_FILTER_TYPE_DEFAULT);

    png_byte ** row_pointers = (png_byte **)png_malloc (p_png, WINDOW_HEIGHT * sizeof (png_byte*));

    for (size_t y = 0; y < WINDOW_HEIGHT; ++y) {
        png_byte *row = (png_byte *)png_malloc (p_png, sizeof (uint8_t) * WINDOW_WIDTH * pixel_size);
        row_pointers[y] = row;
        for (size_t x = 0; x < WINDOW_WIDTH; ++x) {
            *row++ = framebuffer[(y * WINDOW_WIDTH + x) * 4 + 2];
            *row++ = framebuffer[(y * WINDOW_WIDTH + x) * 4 + 1];
            *row++ = framebuffer[(y * WINDOW_WIDTH + x) * 4 + 0];
        }
    }

    png_init_io (p_png, p_file);
    png_set_rows (p_png, p_info, row_pointers);
    png_write_png (p_png, p_info, PNG_TRANSFORM_IDENTITY, NULL);

    for (size_t y = 0; y < WINDOW_HEIGHT; y++) {
        png_free (p_png, row_pointers[y]);
    }
    png_free (p_png, row_pointers);

    png_destroy_write_struct(&p_png, &p_info);

    fclose(p_file);
}
