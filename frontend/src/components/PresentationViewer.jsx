import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  Download,
  FileText,
  Video,
  ZoomIn,
  ZoomOut,
  RotateCw,
  Maximize,
  AlertCircle,
  Eye,
  ExternalLink,
} from 'lucide-react';

const PresentationViewer = ({ 
  file, 
  session = null, 
  showDownload = true, 
  showMetadata = true,
  className = '' 
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [zoom, setZoom] = useState(100);

  useEffect(() => {
    if (file) {
      setLoading(false);
    }
  }, [file]);

  if (!file) {
    return (
      <Card className={className}>
        <CardContent className="p-8 text-center">
          <FileText className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No file uploaded</h3>
          <p className="text-gray-500">Upload a presentation file to view it here.</p>
        </CardContent>
      </Card>
    );
  }

  const getFileType = () => {
    const extension = file.original_filename.toLowerCase().split('.').pop();
    switch (extension) {
      case 'pdf':
        return 'pdf';
      case 'ppt':
      case 'pptx':
        return 'powerpoint';
      case 'mp4':
      case 'mov':
        return 'video';
      default:
        return 'unknown';
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-AU', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const handleDownload = () => {
    // In a real application, this would trigger a download from the server
    const link = document.createElement('a');
    link.href = `/api/sessions/files/${file.id}/download`;
    link.download = file.original_filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleFullscreen = () => {
    // In a real application, this would open the file in fullscreen mode
    window.open(`/api/sessions/files/${file.id}/view`, '_blank');
  };

  const fileType = getFileType();

  const renderViewer = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading presentation...</p>
          </div>
        </div>
      );
    }

    if (error) {
      return (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      );
    }

    switch (fileType) {
      case 'pdf':
        return (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setZoom(Math.max(50, zoom - 25))}
                  disabled={zoom <= 50}
                >
                  <ZoomOut className="h-3 w-3" />
                </Button>
                <span className="text-sm text-muted-foreground">{zoom}%</span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setZoom(Math.min(200, zoom + 25))}
                  disabled={zoom >= 200}
                >
                  <ZoomIn className="h-3 w-3" />
                </Button>
              </div>
              <Button variant="outline" size="sm" onClick={handleFullscreen}>
                <Maximize className="mr-1 h-3 w-3" />
                Fullscreen
              </Button>
            </div>
            
            <div className="border rounded-lg overflow-hidden bg-gray-50">
              <div className="h-96 flex items-center justify-center">
                <div className="text-center">
                  <FileText className="mx-auto h-16 w-16 text-red-500 mb-4" />
                  <h3 className="text-lg font-medium mb-2">PDF Preview</h3>
                  <p className="text-muted-foreground mb-4">
                    {file.original_filename}
                  </p>
                  <div className="space-x-2">
                    <Button variant="outline" onClick={handleFullscreen}>
                      <Eye className="mr-1 h-3 w-3" />
                      View PDF
                    </Button>
                    {showDownload && (
                      <Button variant="outline" onClick={handleDownload}>
                        <Download className="mr-1 h-3 w-3" />
                        Download
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        );

      case 'powerpoint':
        return (
          <div className="space-y-4">
            <div className="border rounded-lg overflow-hidden bg-gray-50">
              <div className="h-96 flex items-center justify-center">
                <div className="text-center">
                  <FileText className="mx-auto h-16 w-16 text-orange-500 mb-4" />
                  <h3 className="text-lg font-medium mb-2">PowerPoint Presentation</h3>
                  <p className="text-muted-foreground mb-4">
                    {file.original_filename}
                  </p>
                  <div className="space-x-2">
                    <Button variant="outline" onClick={handleFullscreen}>
                      <ExternalLink className="mr-1 h-3 w-3" />
                      Open in Viewer
                    </Button>
                    {showDownload && (
                      <Button variant="outline" onClick={handleDownload}>
                        <Download className="mr-1 h-3 w-3" />
                        Download
                      </Button>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    PowerPoint files can be viewed in the browser or downloaded for offline viewing
                  </p>
                </div>
              </div>
            </div>
          </div>
        );

      case 'video':
        return (
          <div className="space-y-4">
            <div className="border rounded-lg overflow-hidden bg-black">
              <div className="h-96 flex items-center justify-center">
                <div className="text-center text-white">
                  <Video className="mx-auto h-16 w-16 text-blue-400 mb-4" />
                  <h3 className="text-lg font-medium mb-2">Video Presentation</h3>
                  <p className="text-gray-300 mb-4">
                    {file.original_filename}
                  </p>
                  <div className="space-x-2">
                    <Button variant="outline" onClick={handleFullscreen}>
                      <Eye className="mr-1 h-3 w-3" />
                      Play Video
                    </Button>
                    {showDownload && (
                      <Button variant="outline" onClick={handleDownload}>
                        <Download className="mr-1 h-3 w-3" />
                        Download
                      </Button>
                    )}
                  </div>
                  <p className="text-xs text-gray-400 mt-2">
                    Click to play the video presentation
                  </p>
                </div>
              </div>
            </div>
          </div>
        );

      default:
        return (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              This file type cannot be previewed in the browser. You can download it to view locally.
            </AlertDescription>
          </Alert>
        );
    }
  };

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center">
            {fileType === 'pdf' && <FileText className="mr-2 h-5 w-5 text-red-500" />}
            {fileType === 'powerpoint' && <FileText className="mr-2 h-5 w-5 text-orange-500" />}
            {fileType === 'video' && <Video className="mr-2 h-5 w-5 text-blue-500" />}
            Presentation Viewer
          </CardTitle>
          {showDownload && (
            <Button variant="outline" size="sm" onClick={handleDownload}>
              <Download className="mr-1 h-3 w-3" />
              Download
            </Button>
          )}
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {renderViewer()}
        
        {showMetadata && (
          <>
            <Separator />
            <div className="space-y-3">
              <h4 className="font-medium">File Information</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Filename:</span>
                  <p className="font-medium">{file.original_filename}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">File Size:</span>
                  <p className="font-medium">{formatFileSize(file.file_size)}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Upload Date:</span>
                  <p className="font-medium">{formatDate(file.upload_date)}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Version:</span>
                  <p className="font-medium">
                    <Badge variant="secondary">v{file.version}</Badge>
                  </p>
                </div>
              </div>
              
              {session && (
                <div className="pt-2 border-t">
                  <span className="text-muted-foreground">Session:</span>
                  <p className="font-medium">{session.title}</p>
                  {session.upload_comments && (
                    <div className="mt-2">
                      <span className="text-muted-foreground">Upload Comments:</span>
                      <p className="text-sm mt-1 p-2 bg-gray-50 rounded">{session.upload_comments}</p>
                    </div>
                  )}
                </div>
              )}
              
              <div className="pt-2 border-t">
                <span className="text-muted-foreground">File Hash:</span>
                <p className="text-xs font-mono text-gray-600 break-all">{file.file_hash}</p>
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default PresentationViewer;

