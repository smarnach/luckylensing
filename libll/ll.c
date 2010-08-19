#include "ll.h"
#include <math.h>
#include <stdlib.h>

extern void
ll_init_magpattern_params(struct ll_magpattern_param_t *params,
                          const struct ll_lenses_t *lenses,
                          const struct ll_rect_t *region,
                          unsigned xpixels, unsigned ypixels)
{
    params->lenses = *lenses;
    params->region = *region;
    params->xpixels = xpixels;
    params->ypixels = ypixels;
    params->pixels_per_width = xpixels / region->width;
    params->pixels_per_height = ypixels / region->height;
}

extern void
ll_init_rayshooter(struct ll_rayshooter_t *rs,
                   struct ll_magpattern_param_t *params)
{
    rs->params = params;
    rs->kernel = LL_KERNEL_BILINEAR;
    rs->refine = 15;
    rs->refine_final = 25;
    rs->cancel = false;
}

extern void
ll_cancel_rayshooter(struct ll_rayshooter_t *rs)
{
    rs->cancel = true;
}

extern int __attribute__ ((hot))
ll_shoot_single_ray(const struct ll_magpattern_param_t *params,
                    double x, double y, double *mag_x, double *mag_y)
{
    struct ll_lens_t *lens = params->lenses.lens;
    double x_deflected = x, y_deflected = y;
    for(unsigned i = 0; i < params->lenses.num_lenses; ++i)
    {
        double dx = x - lens[i].x;
        double dy = y - lens[i].y;
        double theta_squared = dx*dx + dy*dy;
        double deflection = lens[i].mass / theta_squared;
        x_deflected -= dx * deflection;
        y_deflected -= dy * deflection;
    }
    *mag_x = (x_deflected - params->region.x) * params->pixels_per_width;
    *mag_y = (y_deflected - params->region.y) * params->pixels_per_height;
    return (((0 <= *mag_x)     ) | ((*mag_x < params->xpixels) << 1) |
            ((0 <= *mag_y) << 2) | ((*mag_y < params->ypixels) << 3));
}

extern void
ll_rayshoot_rect(const struct ll_magpattern_param_t *params, int *magpat,
                 const struct ll_rect_t *rect, int xrays, int yrays)
{
    double width_per_xrays = rect->width / xrays;
    double height_per_yrays = rect->height / yrays;
    double mag_x, mag_y;
    for (int j = 0; j < yrays; ++j)
        for (int i = 0; i < xrays; ++i)
            if (ll_shoot_single_ray(params,
                                    rect->x + i*width_per_xrays,
                                    rect->y + j*height_per_yrays,
                                    &mag_x, &mag_y) == 0x0F)
                ++magpat[(int)mag_y*params->xpixels + (int)mag_x];
}

static void __attribute__ ((hot))
_ll_rayshoot_bilinear(const struct ll_magpattern_param_t *params, int *magpat,
                      double coords[4][2], bool hit_all, int refine)
{
    double inv_refine = 1.0/refine;
    double ldown_x = (coords[2][0] - coords[0][0]) * inv_refine;
    double ldown_y = (coords[2][1] - coords[0][1]) * inv_refine;
    double rdown_x = (coords[3][0] - coords[1][0]) * inv_refine;
    double rdown_y = (coords[3][1] - coords[1][1]) * inv_refine;
    double right_x = (coords[1][0] - coords[0][0]) * inv_refine;
    double right_y = (coords[1][1] - coords[0][1]) * inv_refine;
    double update_x = (rdown_x - ldown_x) * inv_refine;
    double update_y = (rdown_y - ldown_y) * inv_refine;
    double sx = coords[0][0];
    double sy = coords[0][1];
    if (hit_all)
        for (int j = 0; j < refine; ++j)
        {
            double x = sx;
            double y = sy;
            for (int i = 0; i < refine; ++i)
            {
                ++magpat[(int)y*params->xpixels + (int)x];
                x += right_x;
                y += right_y;
            }
            sx += ldown_x;
            sy += ldown_y;
            right_x += update_x;
            right_y += update_y;
        }
    else
        for (int j = 0; j < refine; ++j)
        {
            double x = sx;
            double y = sy;
            int i = 0;
            while ((x < 0.0 || x >= params->xpixels ||
                    y < 0.0 || y >= params->ypixels) &&
                   i < refine)
            {
                x += right_x;
                y += right_y;
                ++i;
            }
            while (i < refine &&
                   x >= 0.0 && x < params->xpixels &&
                   y >= 0.0 && y < params->ypixels)
            {
                ++magpat[(int)y*params->xpixels + (int)x];
                x += right_x;
                y += right_y;
                ++i;
            }
            sx += ldown_x;
            sy += ldown_y;
            right_x += update_x;
            right_y += update_y;
        }
}

static void __attribute__ ((hot))
_ll_rayshoot_triangulated(const struct ll_magpattern_param_t *params, float *magpat,
                          double rect_area, double tri_vertices[4][2])
{
    for (int triangle = 0; triangle < 2; ++triangle)
    {
        if (triangle)
        {
            tri_vertices[0][0] = tri_vertices[3][0];
            tri_vertices[0][1] = tri_vertices[3][1];
        }

        // Get minimum and maximum x coordinate in the magpattern
        bool single_pixel_optimization = true;
        int min = 0, max = 0;
        if (tri_vertices[1][0] < tri_vertices[0][0])
            min = 1;
        else
            max = 1;
        if (tri_vertices[2][0] < tri_vertices[min][0])
            min = 2;
        if (tri_vertices[2][0] > tri_vertices[max][0])
            max = 2;
        int mag_x0 = (int)(tri_vertices[min][0] + 1.0) - 1;
        if (mag_x0 >= (int)params->xpixels)
            continue;
        if (mag_x0 < -1)
        {
            mag_x0 = -1;
            single_pixel_optimization = false;
        }
        if (tri_vertices[max][0] < 0.0)
            continue;
        int mag_x1 = tri_vertices[max][0];
        if (mag_x1 >= (int)params->xpixels)
        {
            mag_x1 = params->xpixels - 1;
            single_pixel_optimization = false;
        }

        // Get minimum and maximum y coordinate in the magpattern
        min = 0, max = 0;
        if (tri_vertices[1][1] < tri_vertices[0][1])
            min = 1;
        else
            max = 1;
        if (tri_vertices[2][1] < tri_vertices[min][1])
            min = 2;
        if (tri_vertices[2][1] > tri_vertices[max][1])
            max = 2;
        int mag_y0 = (int)(tri_vertices[min][1] + 1.0) - 1;
        if (mag_y0 >= (int)params->ypixels)
            continue;
        if (mag_y0 < 0)
        {
            mag_y0 = 0;
            single_pixel_optimization = false;
        }
        if (tri_vertices[max][1] < 0.0)
            continue;
        int mag_y1 = tri_vertices[max][1];
        if (mag_y1 >= (int)params->ypixels)
        {
            mag_y1 = params->ypixels - 1;
            single_pixel_optimization = false;
        }
        double pixel_area = 0.5 * rect_area *
            params->pixels_per_width * params->pixels_per_height;
        double magnification =  pixel_area /
            ((tri_vertices[1][0]-tri_vertices[0][0]) *
             (tri_vertices[2][1]-tri_vertices[0][1]) -
             (tri_vertices[1][1]-tri_vertices[0][1]) *
             (tri_vertices[2][0]-tri_vertices[0][0]));

        // Render the triangle
        if (single_pixel_optimization && mag_x0 == mag_x1 && mag_y0 == mag_y1)
        {
            // The triangle is completely contained in a single pixel,
            // so we can take a shortcut
            magpat[mag_y0*params->xpixels + mag_x0] += pixel_area;
            continue;
        }
        double vertices[11][2];
        for (int k = 0, lastk = 2; k < 3; lastk = k, ++k)
        {
            vertices[k][0] = tri_vertices[k][0];
            vertices[k][1] = tri_vertices[k][1];
        }
        for (int y = mag_y0; y <= mag_y1; ++y)
        {
            int vertex_indices[5][2];
            vertex_indices[0][0] = 2; vertex_indices[0][1] = 0;
            vertex_indices[1][0] = 0; vertex_indices[1][1] = 1;
            vertex_indices[2][0] = 1; vertex_indices[2][1] = 2;
            int valid_edges = 0x07;
            int num_edges = 3;

            for (int k = 0; k < 2; ++k)
            {
                double yi = y + k;
                int edge_idx = 3 + k;
                int vertex_idx = 3 + 2*k;
                double sgn = 1.0;
                if (k)
                    sgn = -1.0;
                for (int v0 = 2, v1 = 0; v1 < 3; v0 = v1, ++v1)
                {
                    double a0 = sgn * (yi - vertices[v0][1]);
                    double a1 = sgn * (yi - vertices[v1][1]);
                    if (a0 < 0.0)
                    {
                        if (a1 >= 0.0)
                        {
                            double t = a0 / (a0-a1);
                            vertices[vertex_idx][0] = vertices[v0][0] +
                                t*(vertices[v1][0] - vertices[v0][0]);
                            vertices[vertex_idx][1] = yi;
                            vertex_indices[v1][1] = vertex_idx;
                            vertex_indices[edge_idx][0] = vertex_idx;
                            valid_edges |= 1 << edge_idx;
                            ++num_edges;
                        }
                    } else {
                        if (a1 < 0.0)
                        {
                            double t = a0 / (a0-a1);
                            vertices[vertex_idx+1][0] = vertices[v0][0] +
                                t*(vertices[v1][0] - vertices[v0][0]);
                            vertices[vertex_idx+1][1] = yi;
                            vertex_indices[v1][0] = vertex_idx+1;
                            vertex_indices[edge_idx][1] = vertex_idx+1;
                        } else {
                            valid_edges &= ~(1 << v1);
                            --num_edges;
                        }
                    }
                }
            }

            int actions = 0;
            for (int x = mag_x0; x <= mag_x1; ++x)
            {
                int vertex_indices2[7][2];
                for (int i = 0; i < 5; ++i)
                {
                    vertex_indices2[i][0] = vertex_indices[i][0];
                    vertex_indices2[i][1] = vertex_indices[i][1];
                }
                int valid_edges2 = valid_edges;
                int num_edges2 = num_edges;

                if (actions)
                {
                    int idx_offset = (x&1) << 1;
                    for (int i = 0; i < 5; ++i)
                    {
                        switch (actions>>(i<<1) & 3)
                        {
                        case 1:
                        {
                            int vertex_idx = 7 + idx_offset;
                            vertex_indices2[i][1] = vertex_idx;
                            vertex_indices2[5][0] = vertex_idx;
                            valid_edges2 |= 1 << 5;
                            ++num_edges2;
                            break;
                        }
                        case 2:
                        {
                            int vertex_idx = 8 + idx_offset;
                            vertex_indices2[i][0] = vertex_idx;
                            vertex_indices2[5][1] = vertex_idx;
                            break;
                        }
                        case 3:
                        {
                            valid_edges2 &= ~(1 << i);
                            --num_edges2;
                            valid_edges &= ~(1 << i);
                            --num_edges;
                            break;
                        }
                        }
                    }
                }
                double xi = x + 1;
                int idx_offset = ((x&1) ^ 1) << 1;
                actions = 0;
                for(int i = 0; i < 5; ++i)
                {
                    if (!(valid_edges2 & 1<<i))
                        continue;
                    int v0 = vertex_indices2[i][0];
                    int v1 = vertex_indices2[i][1];
                    double a0 = vertices[v0][0] - xi;
                    double a1 = vertices[v1][0] - xi;
                    if (a0 < 0.0)
                    {
                        if (a1 >= 0.0)
                        {
                            actions |= 2 << (i<<1);
                            int vertex_idx = 8 + idx_offset;
                            double t = a0 / (a0-a1);
                            vertices[vertex_idx][0] = xi;
                            vertices[vertex_idx][1] = vertices[v0][1] +
                                t*(vertices[v1][1] - vertices[v0][1]);
                            vertex_indices2[i][1] = vertex_idx;
                            vertex_indices2[6][0] = vertex_idx;
                            valid_edges2 |= 1 << 6;
                            ++num_edges2;
                        } else {
                            actions |= 3 << (i<<1);
                        }
                    } else {
                        if (a1 < 0.0)
                        {
                            actions |= 1 << (i<<1);
                            int vertex_idx = 7 + idx_offset;
                            double t = a0 / (a0-a1);
                            vertices[vertex_idx][0] = xi;
                            vertices[vertex_idx][1] = vertices[v0][1] +
                                t*(vertices[v1][1] - vertices[v0][1]);
                            vertex_indices2[i][0] = vertex_idx;
                            vertex_indices2[6][1] = vertex_idx;
                        } else {
                            valid_edges2 &= ~(1 << i);
                            --num_edges2;
                        }
                    }
                }
                if (num_edges2 <= 1)
                {
                    if (num_edges <= 1)
                        break;
                    double min_x_d = mag_x1;
                    for (int i = 0; i < 5; ++i)
                    {
                        if (!(valid_edges & 1<<i))
                            continue;
                        for (int k = 0; k < 2; ++k)
                        {
                            double tmp_x = vertices[vertex_indices[i][k]][0];
                            if (tmp_x < min_x_d)
                                min_x_d = tmp_x;
                        }
                    }
                    int min_x = (int)min_x_d - 1;
                    if (x < min_x)
                        x = min_x;
                    continue;
                }
                if (num_edges2 >= 3 && x >= 0)
                {
                    double area = 0.0;
                    double x0 = vertices[0][0];
                    double y0 = vertices[0][1];
                    for(int i = 0; i < 7; ++i)
                        if (valid_edges2 & 1<<i)
                        {
                            int i0 = vertex_indices2[i][0];
                            int i1 = vertex_indices2[i][1];
                            area += (vertices[i0][0]-x0) * (vertices[i1][1]-y0)
                                - (vertices[i0][1]-y0) * (vertices[i1][0]-x0);
                        }
                    magpat[y*params->xpixels + x] += area * magnification;
                }
            }
        }
    }
}

static void
_ll_rayshoot_level1(const struct ll_rayshooter_t *rs, void *magpat,
                    const struct ll_rect_t *rect, int xrays, int yrays)
{
    double *mag_coords = malloc((xrays+1)*(yrays+1) * 2*sizeof(double));
    int *hit = malloc((xrays+1)*(yrays+1) * sizeof(int));
    double width_per_xrays = rect->width / xrays;
    double height_per_yrays = rect->height / yrays;
    for (int j = 0, m = 0; j <= yrays; ++j)
        for (int i = 0; i <= xrays; ++i, ++m)
            hit[m] = ll_shoot_single_ray(rs->params,
                                         rect->x + i*width_per_xrays,
                                         rect->y + j*height_per_yrays,
                                         mag_coords + (m<<1),
                                         mag_coords + (m<<1) + 1);
    int xrays2 = 2*xrays + 2;
    double rect_area = width_per_xrays * height_per_yrays;
    for (int j = 0, m = 0; j < yrays; ++j, ++m)
        for (int i = 0; i < xrays; ++i, ++m)
            if ((hit[m] | hit[m+1] | hit[m+xrays+1] | hit[m+xrays+2]) == 0x0F)
            {
                int n = m << 1;
                double local_coords[4][2] =
                    {{mag_coords[n], mag_coords[n+1]},
                     {mag_coords[n+2], mag_coords[n+3]},
                     {mag_coords[n+xrays2], mag_coords[n+xrays2+1]},
                     {mag_coords[n+xrays2+2], mag_coords[n+xrays2+3]}};
                switch (rs->kernel)
                {
                case LL_KERNEL_SIMPLE:
                {
                    double x = rect->x + i*width_per_xrays;
                    double y = rect->y + j*height_per_yrays;
                    struct ll_rect_t subrect
                        = {x, y, width_per_xrays, height_per_yrays};
                    ll_rayshoot_rect(rs->params, (int*)magpat, &subrect,
                                     rs->refine_final, rs->refine_final);
                    break;
                }
                case LL_KERNEL_BILINEAR:
                {
                    bool hit_all = (hit[m] & hit[m+1] & hit[m+xrays+1] &
                                    hit[m+xrays+2]) == 0x0F;
                    _ll_rayshoot_bilinear(rs->params, (int*)magpat,
                                          local_coords, hit_all,
                                          rs->refine_final);
                    break;
                }
                case LL_KERNEL_TRIANGULATED:
                    _ll_rayshoot_triangulated(rs->params, (float*)magpat,
                                              rect_area, local_coords);
                    break;
                }
            }
    free(hit);
    free(mag_coords);
}

static void
_ll_rayshoot_recursively(const struct ll_rayshooter_t *rs, void *magpat,
                         const struct ll_rect_t *rect, int xrays, int yrays,
                         unsigned level, double *progress)
{
    if (rs->cancel)
        return;
    if (level > 1)
    {
        struct ll_patches_t patches =
            { *rect, xrays, yrays, level, rect->width/xrays, rect->height/yrays,
              .hit = malloc(xrays*yrays * sizeof(char)), .num_patches = 0};
        ll_get_subpatches(rs->params, &patches);
        ll_rayshoot_subpatches(rs, magpat, &patches, progress);
        free(patches.hit);
    }
    else
        _ll_rayshoot_level1(rs, magpat, rect, xrays, yrays);
}

extern void
ll_get_subpatches(const struct ll_magpattern_param_t *params,
                  struct ll_patches_t *patches)
{
    int xrays = patches->xrays;
    int yrays = patches->yrays;
    int *hit = malloc((xrays+3)*(yrays+3) * sizeof(int));
    for (int j = -1, m = 0; j <= yrays+1; ++j)
        for (int i = -1; i <= xrays+1; ++i, ++m)
        {
            double mag_x, mag_y;
            hit[m] = ll_shoot_single_ray(
                params,
                patches->rect.x + i*patches->width_per_xrays,
                patches->rect.y + j*patches->height_per_yrays,
                &mag_x, &mag_y);
        }
    patches->num_patches = 0;
    char* hit_patches = patches->hit;
    for (int j = 0, m = xrays+4, n = 0; j < yrays; ++j, m += 3)
        for (int i = 0; i < xrays; ++i, ++m, ++n)
        {
            hit_patches[n] = (hit[m-xrays-3] | hit[m-xrays-2] |
                              hit[m-1] | hit[m] | hit[m+1] | hit[m+2] |
                              hit[m+xrays+2] | hit[m+xrays+3] |
                              hit[m+xrays+4] | hit[m+xrays+5] |
                              hit[m+2*xrays+6] | hit[m+2*xrays+7]) == 0x0F;
            if (hit_patches[n])
                ++patches->num_patches;
        }
    free(hit);
}

extern void
ll_rayshoot_subpatches(const struct ll_rayshooter_t *rs, void *magpat,
                       const struct ll_patches_t *patches, double *progress)
{
    double progress_inc = 1.0 / patches->num_patches;
    for (int j = 0, n = 0; j < patches->yrays; ++j)
        for (int i = 0; i < patches->xrays; ++i, ++n)
            if (patches->hit[n])
            {
                double x = patches->rect.x + i*patches->width_per_xrays;
                double y = patches->rect.y + j*patches->height_per_yrays;
                struct ll_rect_t subrect
                    = {x, y, patches->width_per_xrays, patches->height_per_yrays};
                _ll_rayshoot_recursively(rs, magpat, &subrect, rs->refine,
                                         rs->refine, patches->level-1, 0);
                if (progress)
                    *progress += progress_inc;
            }
}

static void
_ll_scale_magpattern(const struct ll_rayshooter_t *rs, void *magpat,
                     const struct ll_rect_t *rect, int xrays, int yrays,
                     unsigned level)
{
    switch (rs->kernel)
    {
    case LL_KERNEL_SIMPLE:
    case LL_KERNEL_BILINEAR:
    {
        unsigned pixels = rs->params->xpixels * rs->params->ypixels;
        double density = xrays * yrays;
        for (unsigned i = 0; i < level - 1; ++i)
            density *= rs->refine * rs->refine;
        density *= rs->refine_final * rs->refine_final;
        density *= rs->params->region.width * rs->params->region.height;
        density /= rect->width * rect->height * pixels;
        density = 1.0/density;
        float *fpat = magpat;
        int *ipat = magpat;
        for (unsigned i = 0; i < pixels; ++i)
            fpat[i] = ipat[i] * density;
        break;
    }
    case LL_KERNEL_TRIANGULATED:
        break;
    }
}

extern void
ll_finalise_subpatches(const struct ll_rayshooter_t *rs, void *magpat,
                       const struct ll_patches_t *patches)
{
    _ll_scale_magpattern(rs, magpat, &patches->rect,
                         patches->xrays, patches->yrays, patches->level);
}

extern void
ll_rayshoot(const struct ll_rayshooter_t *rs, void *magpat,
            const struct ll_rect_t *rect, int xrays, int yrays,
            unsigned levels, double *progress)
{
    if (progress)
        *progress = 0.0;
    _ll_rayshoot_recursively(rs, magpat, rect, xrays, yrays,
                             levels - 1, progress);
    _ll_scale_magpattern(rs, magpat, rect, xrays, yrays, levels - 1);
}

extern void
ll_ray_hit_pattern(const struct ll_magpattern_param_t *params, char *buf,
                   const struct ll_rect_t *rect)
{
    double width_per_xrays = rect->width / params->xpixels;
    double height_per_yrays = rect->height / params->ypixels;
    double mag_x, mag_y;
    for (unsigned j = 0; j < params->ypixels; ++j)
        for (unsigned i = 0; i < params->xpixels; ++i)
            buf[j*params->xpixels + i] = 255 *
                (ll_shoot_single_ray(
                    params, rect->x + i*width_per_xrays,
                    rect->y + j*height_per_yrays, &mag_x, &mag_y) == 0x0F);
}

extern void
ll_source_images(const struct ll_magpattern_param_t *params, char *buf,
                 const struct ll_rect_t *rect, int xrays, int yrays,
                 int refine, double source_x, double source_y, double source_r)
{
    double r_squared = source_r*source_r;
    double width_per_xrays = rect->width / xrays;
    double height_per_yrays = rect->height / yrays;
    double x_inc = width_per_xrays / refine;
    double y_inc = height_per_yrays / refine;
    int buf_inc = 255 / (refine*refine);
    for (int j = 0, m = 0; j < xrays; ++j)
        for (int i = 0; i < yrays; ++i, ++m)
        {
            double x0 = rect->x + i*width_per_xrays;
            double y = rect->y + j*height_per_yrays;
            for (int k = 0; k < refine; ++k)
            {
                double x = x0;
                for (int l = 0; l < refine; ++l)
                {
                    double mag_x, mag_y;
                    ll_shoot_single_ray(params, x, y, &mag_x, &mag_y);
                    double dx = source_x - mag_x;
                    double dy = source_y - mag_y;
                    if (dx*dx + dy*dy < r_squared)
                        buf[m] += buf_inc;
                    x += x_inc;
                }
                y += y_inc;
            }
        }
}

static void
_ll_get_magpattern_minmax(const float *magpat, unsigned size, float min,
                          float max, double *logmin, double* logmax)
{
    if (min < 0.0 || max < 0.0 || min == max)
    {
        min = __FLT_MAX__;
        max = 0.0;
        for(unsigned i = 0; i < size; ++i)
        {
            if (magpat[i] < min)
                min = magpat[i];
            if (magpat[i] > max)
                max = magpat[i];
        }
    }
    *logmin = log(min+1e-10);
    *logmax = log(max+1e-10);
}

extern void
ll_render_magpattern_greyscale(const float *magpat, char *buf, unsigned size,
                               float min, float max)
{
    double logmin, logmax;
    _ll_get_magpattern_minmax(magpat, size, min, max, &logmin, &logmax);
    double logdiff = logmax - logmin;
    if (logdiff == 0.0)
        return;
    double factor = 255 / logdiff;
    for(unsigned i = 0; i < size; ++i)
    {
        double log_mag = log(magpat[i]+1e-10) - logmin;
        if (log_mag <= 0.0)
            buf[i] = 0;
        else if (log_mag >= logdiff)
            buf[i] = 255;
        else
            buf[i] = log_mag*factor;
    }
}

extern void
ll_render_magpattern_gradient(const float *magpat, char *buf, unsigned size,
                              float min, float max,
                              const unsigned char colors[][3],
                              const unsigned *steps)
{
    double logmin, logmax;
    _ll_get_magpattern_minmax(magpat, size, min, max, &logmin, &logmax);
    double logdiff = logmax - logmin;
    if (logdiff == 0.0)
        return;
    unsigned total_colors = 1;
    for (int segment = 0; steps[segment]; ++segment)
        total_colors += steps[segment];
    char (*all_colors)[3] = malloc(3 * total_colors * sizeof(char));
    all_colors[0][0] = colors[0][0];
    all_colors[0][1] = colors[0][1];
    all_colors[0][2] = colors[0][2];
    unsigned pos = 1;
    for (int segment = 0; steps[segment]; ++segment)
    {
        int diff[3];
        diff[0] = colors[segment+1][0] - colors[segment][0];
        diff[1] = colors[segment+1][1] - colors[segment][1];
        diff[2] = colors[segment+1][2] - colors[segment][2];
        for (unsigned i = 1; i <= steps[segment]; ++i)
        {
            all_colors[pos][0] = colors[segment][0] + i*diff[0]/steps[segment];
            all_colors[pos][1] = colors[segment][1] + i*diff[1]/steps[segment];
            all_colors[pos][2] = colors[segment][2] + i*diff[2]/steps[segment];
            ++pos;
        }
    }
    double factor = (total_colors-1) / logdiff;
    for(unsigned i = 0; i < size; ++i)
    {
        unsigned color;
        double log_mag = log(magpat[i]+1e-10) - logmin;
        if (log_mag <= 0.0)
            color = 0;
        else if (log_mag >= logdiff)
            color = total_colors - 1;
        else
            color = log_mag*factor;
        buf[3*i] = all_colors[color][0];
        buf[3*i + 1] = all_colors[color][1];
        buf[3*i + 2] = all_colors[color][2];
    }
    free(all_colors);
}

extern void
ll_light_curve(const struct ll_magpattern_param_t *params, const float *magpat,
               double *curve, unsigned num_points,
               double x0, double y0, double x1, double y1)
{
    double mag_x = (x0 - params->region.x) * params->pixels_per_width;
    double mag_y = (y0 - params->region.y) * params->pixels_per_height;
    double dx = (x1 - x0) * params->pixels_per_width / (num_points - 1);
    double dy = (y1 - y0) * params->pixels_per_height / (num_points - 1);
    for (unsigned i = 0; i < num_points; ++i)
    {
        int ix = mag_x;
        int iy = mag_y;
        int index = iy*params->xpixels + ix;
        double frac_x = mag_x - ix;
        double frac_y = mag_y - iy;
        curve[i] = (1.0 - frac_x) * (1.0 - frac_y) * magpat[index]
            + frac_x * (1.0 - frac_y) * magpat[index+1]
            + (1.0 - frac_x) * frac_y * magpat[index+params->xpixels]
            + frac_x * frac_y * magpat[index+params->xpixels+1];
        mag_x += dx;
        mag_y += dy;
    }
}
